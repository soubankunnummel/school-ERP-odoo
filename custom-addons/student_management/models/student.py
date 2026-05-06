# -*- coding: utf-8 -*-
"""
student.py — Core Student Model
================================
MERN equivalent: User/Student MongoDB collection + Mongoose schema
Odoo concepts covered:
  - Many2one  (class_id)        → like a FK / ref in Mongo
  - Many2many (subject_ids)     → like an array of refs
  - One2many  (attendance_ids)  → virtual back-relation
  - @api.depends                → like React computed state / useMemo
  - @api.constrains             → like Zod / Joi validation
  - @api.onchange               → like onChange handler in React
  - Selection field             → like an enum / status field
  - Binary field                → stores avatar image (base64)
  - External API call           → fetches avatar from dummyjson.com
"""

import hashlib
import logging
import requests

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Student(models.Model):
    _name = 'school.student'
    _description = 'Student'
    _inherit = ['mail.thread', 'mail.activity.mixin']   # adds Chatter + Activities
    _order = 'name asc'

    # ------------------------------------------------------------------ #
    #  Basic Fields                                                        #
    # ------------------------------------------------------------------ #
    name = fields.Char(string='Full Name', required=True, tracking=True)
    roll_number = fields.Char(string='Roll Number', copy=False, readonly=True,
                              default='New')
    age = fields.Integer(string='Age', tracking=True)
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ], string='Gender')
    date_of_birth = fields.Date(string='Date of Birth')
    address = fields.Text(string='Address')

    # Avatar — fetched from external API (dummyjson.com)
    # MERN equivalent: storing a URL or base64 image in MongoDB
    avatar_url = fields.Char(string='Avatar URL', compute='_compute_avatar_url',
                             store=True)
    avatar_image = fields.Binary(string='Profile Photo', attachment=True)

    # ------------------------------------------------------------------ #
    #  Relational Fields                                                   #
    # ------------------------------------------------------------------ #
    # Many2one → "belongs to one class"   (MERN: class_id: ObjectId ref)
    class_id = fields.Many2one('school.class', string='Class', tracking=True,
                               ondelete='set null')

    # Many2many → "enrolled in many subjects"  (MERN: [ObjectId] array)
    subject_ids = fields.Many2many(
        'school.subject',
        'student_subject_rel',   # junction table name
        'student_id',
        'subject_id',
        string='Subjects'
    )

    # One2many → virtual back-relation to attendance records
    # (MERN: populate / virtual field)
    attendance_ids = fields.One2many('school.attendance', 'student_id',
                                     string='Attendance Records')

    # One2many → fee records
    fee_ids = fields.One2many('school.fee', 'student_id', string='Fees')

    # ------------------------------------------------------------------ #
    #  Workflow / State   (MERN: status field + API endpoints)             #
    # ------------------------------------------------------------------ #
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('graduated', 'Graduated'),
    ], string='Status', default='draft', tracking=True, copy=False)

    # ------------------------------------------------------------------ #
    #  Computed Fields  (MERN: useMemo / computed getters)                 #
    # ------------------------------------------------------------------ #
    total_attendance = fields.Integer(
        string='Total Attendance Days',
        compute='_compute_attendance_stats',
        store=True
    )
    present_days = fields.Integer(
        string='Present Days',
        compute='_compute_attendance_stats',
        store=True
    )
    absent_days = fields.Integer(
        string='Absent Days',
        compute='_compute_attendance_stats',
        store=True
    )
    attendance_percentage = fields.Float(
        string='Attendance %',
        compute='_compute_attendance_stats',
        store=True,
        digits=(5, 2)
    )
    subject_count = fields.Integer(
        string='Subject Count',
        compute='_compute_subject_count',
        store=True
    )
    has_fee_discount = fields.Boolean(
        string='Fee Discount Applied',
        compute='_compute_fee_discount',
        store=True
    )
    total_fee_due = fields.Float(
        string='Total Fee Due',
        compute='_compute_total_fee',
        store=True,
        digits=(10, 2)
    )
    active = fields.Boolean(default=True)

    # ------------------------------------------------------------------ #
    #  Sequence / auto roll_number  (MERN: pre-save hook / uuid)          #
    # ------------------------------------------------------------------ #
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('roll_number', 'New') == 'New':
                vals['roll_number'] = self.env['ir.sequence'].next_by_code(
                    'school.student.sequence') or 'STU/0001'
        records = super().create(vals_list)
        # Fetch avatar for each new student
        for rec in records:
            rec._fetch_avatar_from_api()
        return records

    # ------------------------------------------------------------------ #
    #  @api.depends — Computed Methods  (MERN: useEffect with deps)       #
    # ------------------------------------------------------------------ #
    @api.depends('attendance_ids', 'attendance_ids.status')
    def _compute_attendance_stats(self):
        """
        Recomputes whenever attendance records change.
        MERN equivalent:
            const stats = useMemo(() => {
                const present = attendance.filter(a => a.status === 'present').length;
                return { present, percentage: present / attendance.length * 100 };
            }, [attendance]);
        """
        settings = self.env['school.settings'].sudo().get_settings()
        min_pct = settings.min_attendance_percentage if settings else 75.0

        for student in self:
            records = student.attendance_ids
            total = len(records)
            present = len(records.filtered(lambda r: r.status == 'present'))
            absent = total - present
            pct = (present / total * 100) if total else 0.0

            student.total_attendance = total
            student.present_days = present
            student.absent_days = absent
            student.attendance_percentage = pct

    @api.depends('subject_ids')
    def _compute_subject_count(self):
        for student in self:
            student.subject_count = len(student.subject_ids)

    @api.depends('subject_ids')
    def _compute_fee_discount(self):
        """
        Smart Discount: >5 subjects → discount applied.
        MERN: derived field / business rule on the backend.
        """
        settings = self.env['school.settings'].sudo().get_settings()
        threshold = settings.discount_subject_threshold if settings else 5

        for student in self:
            student.has_fee_discount = len(student.subject_ids) > threshold

    @api.depends('fee_ids', 'fee_ids.amount', 'fee_ids.state')
    def _compute_total_fee(self):
        for student in self:
            pending_fees = student.fee_ids.filtered(
                lambda f: f.state in ('pending', 'overdue'))
            student.total_fee_due = sum(pending_fees.mapped('amount'))

    @api.depends('name', 'roll_number')
    def _compute_avatar_url(self):
        """
        External API integration — dummyjson.com avatar API.
        URL format: https://dummyjson.com/icon/HASH/SIZE
        MERN equivalent: axios.get() inside useEffect or a service function.
        """
        for student in self:
            if student.name:
                hash_val = hashlib.md5(
                    (student.name + (student.roll_number or '')).encode()
                ).hexdigest()[:8]
                student.avatar_url = (
                    f"https://dummyjson.com/icon/{hash_val}/150?type=png"
                )
            else:
                student.avatar_url = False

    # ------------------------------------------------------------------ #
    #  @api.constrains — Validation  (MERN: Joi/Zod schema validation)    #
    # ------------------------------------------------------------------ #
    @api.onchange('date_of_birth')
    def _onchange_date_of_birth(self):
        """Auto-calculate age from date_of_birth when it changes."""
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            dob = self.date_of_birth
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            self.age = age

    @api.onchange('age')
    def _onchange_age(self):
        """ When age is entered manually:
    - Clear DOB so user picks it fresh
    - Warn them which birth years are valid
    - Can't auto-fill DOB because we don't know month/day"""           
        if self.age and self.age > 0:
            from datetime import date
            today = date.today()

            year_1 = today.year - self.age
            year_2 = year_1 - 1

            # clear DOB user must pick correclty 
            self.date_of_birth = False

            return {
            'warning': {
                'title': 'Select Date of Birth',
                'message': (
                    f"For age {self.age}, your birth year should be "
                    f"{year_1} or {year_2}.\n"
                    f"Please select the correct date of birth manually."
                )
            }
        }

    @api.constrains('age', 'date_of_birth')
    def _check_age(self):
        """Age must be > 5 and < 30 for a school student."""
        for student in self:
            if student.age and student.age <= 5:
                raise ValidationError("Student age must be greater than 5.")
            if student.age and student.age > 30:
                raise ValidationError("Age seems too high for a school student (max 30).")
            if student.date_of_birth and student.age:
                from datetime import date
                today = date.today()
                dob = student.date_of_birth
                calculated_age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                if calculated_age != student.age:
                    year_1 = today.year - student.age
                    year_2 = year_1 - 1
                    raise ValidationError(
                    f"Age ({student.age}) does not match Date of Birth ({dob}).\n"
                    f"Calculated age from DOB is {calculated_age}.\n"
                    f"For age {student.age}, birth year must be {year_1} or {year_2}."
                )

    @api.constrains('email')
    def _check_email(self):
        for student in self:
            if student.email and '@' not in student.email:
                raise ValidationError(f"Invalid email address: {student.email}")

    # ------------------------------------------------------------------ #
    #  @api.onchange — Reactive Logic  (MERN: onChange event handler)     #
    # ------------------------------------------------------------------ #
    @api.onchange('class_id')
    def _onchange_class_id(self):
        """
        When class changes → auto-assign subjects linked to that class.
        MERN equivalent:
            useEffect(() => {
                if (classId) fetchSubjectsForClass(classId);
            }, [classId]);
        """
        if self.class_id:
            class_subjects = self.class_id.subject_ids
            if class_subjects:
                self.subject_ids = class_subjects
                return {
                    'warning': {
                        'title': 'Subjects Auto-assigned',
                        'message': f"Subjects for class '{self.class_id.name}' have been auto-assigned.",
                    }
                }
        else:
            self.subject_ids = [(5, 0, 0)]  # clear all

    # ------------------------------------------------------------------ #
    #  Workflow Buttons  (MERN: PUT /api/students/:id/confirm)            #
    # ------------------------------------------------------------------ #
    def action_confirm(self):
        """Draft → Confirmed"""
        for rec in self:
            if not rec.class_id:
                raise ValidationError("Please assign a class before confirming.")
            rec.state = 'confirmed'
            rec.message_post(body="Student confirmed and enrolled.")

    def action_graduate(self):
        """Confirmed → Graduated"""
        for rec in self:
            rec.state = 'graduated'
            rec.message_post(body="🎓 Student graduated!")

    def action_reset_draft(self):
        """Back to Draft"""
        for rec in self:
            rec.state = 'draft'

    def action_view_attendance(self):
        return {
        'type': 'ir.actions.act_window',
        'name': 'Attendance',
        'res_model': 'school.attendance',
        'view_mode': 'tree,form',
        'domain': [('student_id', '=', self.id)],
        'context': {'default_student_id': self.id},
    }

    def action_view_fees(self):
        return {
        'type': 'ir.actions.act_window',
        'name': 'Fees',
        'res_model': 'school.fee',
        'view_mode': 'tree,form',
        'domain': [('student_id', '=', self.id)],
        'context': {'default_student_id': self.id},
    }

    def action_view_subjects(self):
        return {
        'type': 'ir.actions.act_window',
        'name': 'Subjects',
        'res_model': 'school.subject',
        'view_mode': 'tree,form',
        'domain': [('student_ids', 'in', self.ids)],
    }
    # ------------------------------------------------------------------ #
    #  External API Call  (MERN: axios/fetch service)                     #
    # ------------------------------------------------------------------ #
    def _fetch_avatar_from_api(self):
        """
        Calls dummyjson.com avatar API to fetch a profile image.
        Format: https://dummyjson.com/icon/HASH/SIZE?type=png

        MERN equivalent:
            const res = await axios.get(`https://dummyjson.com/icon/${hash}/150`);
        """
        for student in self:
            try:
                if not student.name:
                    continue
                hash_val = hashlib.md5(
                    (student.name + (student.roll_number or '')).encode()
                ).hexdigest()[:8]
                url = f"https://dummyjson.com/icon/{hash_val}/150?type=png"

                _logger.info(f"Fetching avatar for student '{student.name}' from {url}")
                response = requests.get(url, timeout=5)

                if response.status_code == 200:
                    import base64
                    student.avatar_image = base64.b64encode(response.content)
                    student.avatar_url = url
                    _logger.info(f"Avatar fetched successfully for {student.name}")
                else:
                    _logger.warning(
                        f"Avatar API returned {response.status_code} for {student.name}"
                    )
            except requests.exceptions.RequestException as e:
                _logger.error(f"Avatar API call failed for {student.name}: {e}")

    def action_refresh_avatar(self):
        """Manual button to re-fetch avatar from API."""
        self._fetch_avatar_from_api()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Avatar Refreshed',
                'message': 'Profile photo fetched from DummyJSON API.',
                'type': 'success',
            }
        }

    # ------------------------------------------------------------------ #
    #  Name Search override  (for better dropdown search UX)             #
    # ------------------------------------------------------------------ #
    @api.model
    def _name_search(self, name='', domain=None, operator='ilike',
                     limit=100, order=None):
        domain = domain or []
        if name:
            domain = [('name', operator, name)] + domain
        return self._search(domain, limit=limit, order=order)

    def name_get(self):
        return [(rec.id, f"[{rec.roll_number}] {rec.name}") for rec in self]
    
    # ------------------------------------------------------------------ #
    #  @api.model cron auto mark absence                                  #
    # ------------------------------------------------------------------ #

    @api.model
    def _cron_auto_mark_absent(self):
        """
        Cron job to automatically mark students as absent if they haven't been marked present.
        """
        from datetime import date, timedelta
        import logging

        _logger = logging.getLogger('school.cron')

        settings = self.env['school.settings'].sudo().get_settings()

        if not settings.auto_mark_absent:
            _logger.info("Cron: Auto-mark absent is disabled in settings.")
            return

        yesterday = date.today() - timedelta(days=1)
        students =  self.search([('state', '=', 'confirmed')])
        count_marked = 0

        for student in students:
            exisisting = self.env['school.attendance'].sudo().search([
                ('student_id', '=', student.id),
                ('date', '=', yesterday)
            ], limit=1)
            
            if not exisisting:
                self.env['school.attendance'].sudo().create({
                    'student_id': student.id,
                    'date': yesterday,
                    'status': 'absent',
                    'note': 'Auto-marked as absent by cron job.'
                })
                count_marked += 1

        _logger.info(f"Cron: Auto-marked {count_marked} students as absent.")
        _logger.info('Cron: marked %s students absent for %s', count_marked, yesterday)
