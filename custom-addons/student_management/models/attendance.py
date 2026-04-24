# -*- coding: utf-8 -*-
"""
attendance.py — Attendance Model
==================================
MERN equivalent: Attendance collection with student ref, date, status
"""
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Attendance(models.Model):
    _name = 'school.attendance'
    _description = 'Student Attendance'
    _order = 'date desc'
    _rec_name = 'student_id'

    # Many2one → attendance belongs to one student
    student_id = fields.Many2one('school.student', string='Student',
                                 required=True, ondelete='cascade')
    class_id = fields.Many2one('school.class', string='Class',
                               related='student_id.class_id', store=True,
                               readonly=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    status = fields.Selection([
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    ], string='Status', required=True, default='present')
    note = fields.Text(string='Note')
    marked_by = fields.Many2one('res.users', string='Marked By',
                                default=lambda self: self.env.user)

    # Prevent duplicate attendance for same student on same date
    _sql_constraints = [
        ('unique_student_date',
         'UNIQUE(student_id, date)',
         'Attendance already marked for this student on this date!')
    ]

    @api.constrains('date')
    def _check_date(self):
        """Don't allow future-dated attendance."""
        today = fields.Date.today()
        for rec in self:
            if rec.date > today:
                raise ValidationError("Cannot mark attendance for a future date.")
