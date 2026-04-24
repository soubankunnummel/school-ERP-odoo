# -*- coding: utf-8 -*-
"""
teacher.py — Teacher Model
===========================
MERN equivalent: Teacher collection / schema
"""
import hashlib
import logging
import requests

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Teacher(models.Model):
    _name = 'school.teacher'
    _description = 'Teacher'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc'

    name = fields.Char(string='Full Name', required=True, tracking=True)
    employee_id = fields.Char(string='Employee ID', copy=False, readonly=True,
                              default='New')
    email = fields.Char(string='Email', required=True)
    phone = fields.Char(string='Phone')
    qualification = fields.Char(string='Qualification')
    experience_years = fields.Integer(string='Experience (Years)')
    avatar_url = fields.Char(string='Avatar URL', compute='_compute_avatar_url', store=True)
    avatar_image = fields.Binary(string='Profile Photo', attachment=True)
    active = fields.Boolean(default=True)

    # Relational
    # One teacher → many subjects  (MERN: [subjectId] array)
    subject_ids = fields.One2many('school.subject', 'teacher_id', string='Subjects Taught')

    # One teacher → many classes
    class_ids = fields.One2many('school.class', 'teacher_id', string='Classes')

    # Computed
    student_count = fields.Integer(string='Total Students',
                                   compute='_compute_student_count', store=True)
    subject_count = fields.Integer(string='Subjects Count',
                                   compute='_compute_counts', store=True)
    class_count = fields.Integer(string='Classes Count',
                                 compute='_compute_counts', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('employee_id', 'New') == 'New':
                vals['employee_id'] = self.env['ir.sequence'].next_by_code(
                    'school.teacher.sequence') or 'TCH/0001'
        records = super().create(vals_list)
        for rec in records:
            rec._fetch_avatar_from_api()
        return records

    @api.depends('name', 'employee_id')
    def _compute_avatar_url(self):
        for teacher in self:
            if teacher.name:
                hash_val = hashlib.md5(
                    ('teacher' + teacher.name + (teacher.employee_id or '')).encode()
                ).hexdigest()[:8]
                teacher.avatar_url = f"https://dummyjson.com/icon/{hash_val}/150?type=png"
            else:
                teacher.avatar_url = False

    @api.depends('class_ids', 'class_ids.student_ids')
    def _compute_student_count(self):
        for teacher in self:
            total = sum(len(cls.student_ids) for cls in teacher.class_ids)
            teacher.student_count = total

    @api.depends('subject_ids', 'class_ids')
    def _compute_counts(self):
        for teacher in self:
            teacher.subject_count = len(teacher.subject_ids)
            teacher.class_count = len(teacher.class_ids)

    @api.constrains('email')
    def _check_email(self):
        for teacher in self:
            if teacher.email and '@' not in teacher.email:
                raise ValidationError(f"Invalid email: {teacher.email}")

    def _fetch_avatar_from_api(self):
        for teacher in self:
            try:
                if not teacher.name:
                    continue
                hash_val = hashlib.md5(
                    ('teacher' + teacher.name).encode()
                ).hexdigest()[:8]
                url = f"https://dummyjson.com/icon/{hash_val}/150?type=png"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    import base64
                    teacher.avatar_image = base64.b64encode(response.content)
            except Exception as e:
                _logger.error(f"Avatar fetch failed for teacher {teacher.name}: {e}")

    def action_refresh_avatar(self):
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

    def name_get(self):
        return [(rec.id, f"[{rec.employee_id}] {rec.name}") for rec in self]

    
    def action_view_students(self):
        return {
        'type': 'ir.actions.act_window',
        'name': 'Students',
        'res_model': 'school.student',
        'view_mode': 'tree,form',
        'domain': [('class_id.teacher_id', '=', self.id)],
    }

    def action_view_subjects(self):
        return {
        'type': 'ir.actions.act_window',
        'name': 'Subjects',
        'res_model': 'school.subject',
        'view_mode': 'tree,form',
        'domain': [('teacher_id', '=', self.id)],
    }

    def action_view_classes(self):
        return {
        'type': 'ir.actions.act_window',
        'name': 'Classes',
        'res_model': 'school.class',
        'view_mode': 'tree,form',
        'domain': [('teacher_id', '=', self.id)],
    }