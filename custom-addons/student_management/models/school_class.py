# -*- coding: utf-8 -*-
"""
school_class.py — Class / Classroom Model
==========================================
MERN equivalent: Class collection with teacher ref and students virtual array
"""
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SchoolClass(models.Model):
    _name = 'school.class'
    _description = 'School Class'
    _order = 'name asc'

    name = fields.Char(string='Class Name', required=True)
    code = fields.Char(string='Class Code')
    grade = fields.Selection([
        ('1', 'Grade 1'), ('2', 'Grade 2'), ('3', 'Grade 3'),
        ('4', 'Grade 4'), ('5', 'Grade 5'), ('6', 'Grade 6'),
        ('7', 'Grade 7'), ('8', 'Grade 8'), ('9', 'Grade 9'),
        ('10', 'Grade 10'), ('11', 'Grade 11'), ('12', 'Grade 12'),
    ], string='Grade')
    section = fields.Char(string='Section', default='A')
    academic_year = fields.Char(string='Academic Year', default='2024-25')
    max_students = fields.Integer(string='Max Students', default=40)
    room_number = fields.Char(string='Room Number')
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)

    # Many2one → class has one teacher (MERN: teacherId ref)
    teacher_id = fields.Many2one('school.teacher', string='Class Teacher',
                                 ondelete='set null')

    # One2many → students in this class (MERN: virtual populate)
    student_ids = fields.One2many('school.student', 'class_id', string='Students')

    # Many2many → subjects taught in this class
    subject_ids = fields.Many2many(
        'school.subject',
        'class_subject_rel',
        'class_id',
        'subject_id',
        string='Subjects'
    )

    # Computed
    student_count = fields.Integer(string='Student Count',
                                   compute='_compute_student_count', store=True)
    is_full = fields.Boolean(string='Class Full',
                             compute='_compute_is_full', store=True)

    @api.depends('student_ids')
    def _compute_student_count(self):
        for cls in self:
            cls.student_count = len(cls.student_ids)

    @api.depends('student_count', 'max_students')
    def _compute_is_full(self):
        for cls in self:
            cls.is_full = cls.student_count >= cls.max_students

    @api.constrains('max_students')
    def _check_max_students(self):
        for cls in self:
            if cls.max_students <= 0:
                raise ValidationError("Max students must be a positive number.")

    def name_get(self):
        return [(rec.id, f"{rec.name} - {rec.section} ({rec.academic_year})")
                for rec in self]

    def action_view_students(self):
        return {
        'type': 'ir.actions.act_window',
        'name': 'Students',
        'res_model': 'school.student',
        'view_mode': 'tree,form',
        'domain': [('class_id', '=', self.id)],
        'context': {'default_class_id': self.id},
    }