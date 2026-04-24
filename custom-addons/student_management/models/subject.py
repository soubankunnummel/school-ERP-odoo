# -*- coding: utf-8 -*-
"""
subject.py — Subject Model
============================
MERN equivalent: Subject collection
"""
from odoo import api, fields, models


class Subject(models.Model):
    _name = 'school.subject'
    _description = 'Subject'
    _order = 'name asc'

    name = fields.Char(string='Subject Name', required=True)
    code = fields.Char(string='Subject Code')
    description = fields.Text(string='Description')
    credit_hours = fields.Float(string='Credit Hours', default=1.0)
    is_elective = fields.Boolean(string='Elective Subject', default=False)
    active = fields.Boolean(default=True)

    # Many2one — subject belongs to one teacher
    teacher_id = fields.Many2one('school.teacher', string='Subject Teacher',
                                 ondelete='set null')

    # Many2many back-relation → students enrolled (auto-created by student model)
    student_ids = fields.Many2many(
        'school.student',
        'student_subject_rel',
        'subject_id',
        'student_id',
        string='Enrolled Students'
    )

    # Computed
    student_count = fields.Integer(string='Student Count',
                                   compute='_compute_student_count', store=True)

    @api.depends('student_ids')
    def _compute_student_count(self):
        for subject in self:
            subject.student_count = len(subject.student_ids)

    def name_get(self):
        return [(rec.id, f"[{rec.code}] {rec.name}" if rec.code else rec.name)
                for rec in self]
    def action_view_enrolled_students(self):
        return {
        'type': 'ir.actions.act_window',
        'name': 'Enrolled Students',
        'res_model': 'school.student',
        'view_mode': 'tree,form',
        'domain': [('subject_ids', 'in', self.ids)],
    }