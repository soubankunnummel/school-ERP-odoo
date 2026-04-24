# -*- coding: utf-8 -*-
"""
bulk_attendance_wizard.py — Bulk Attendance Marking Wizard
============================================================
MERN equivalent: a modal form that sends a POST request
to mark attendance for all students in a class at once.

Odoo Wizard = transient model (not saved permanently)
"""
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class BulkAttendanceWizard(models.TransientModel):
    """
    TransientModel = temporary model (like a modal / dialog state in React).
    Records are auto-deleted after 24 hours.
    """
    _name = 'school.bulk.attendance.wizard'
    _description = 'Bulk Attendance Wizard'

    class_id = fields.Many2one('school.class', string='Class', required=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    default_status = fields.Selection([
        ('present', 'Mark All Present'),
        ('absent', 'Mark All Absent'),
    ], string='Default Status', default='present', required=True)

    line_ids = fields.One2many(
        'school.bulk.attendance.line',
        'wizard_id',
        string='Students'
    )

    @api.onchange('class_id')
    def _onchange_class_id(self):
        """When class selected → populate student lines."""
        if self.class_id:
            lines = []
            for student in self.class_id.student_ids.filtered(
                    lambda s: s.state == 'confirmed'):
                lines.append((0, 0, {
                    'student_id': student.id,
                    'status': self.default_status or 'present',
                }))
            self.line_ids = lines

    @api.onchange('default_status')
    def _onchange_default_status(self):
        """Change all line statuses when default changes."""
        for line in self.line_ids:
            line.status = self.default_status

    def action_submit(self):
        """
        Create attendance records for all lines.
        MERN: handleSubmit → POST /api/attendance/bulk
        """
        if not self.line_ids:
            raise ValidationError("No students found. Please select a class.")

        Attendance = self.env['school.attendance']
        created = 0
        skipped = 0

        for line in self.line_ids:
            # Skip if already marked
            existing = Attendance.search([
                ('student_id', '=', line.student_id.id),
                ('date', '=', self.date),
            ], limit=1)
            if existing:
                skipped += 1
                continue

            Attendance.create({
                'student_id': line.student_id.id,
                'date': self.date,
                'status': line.status,
            })
            created += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Attendance Submitted',
                'message': f"Created: {created} records. Skipped (already exists): {skipped}.",
                'type': 'success',
                'sticky': False,
            }
        }


class BulkAttendanceLine(models.TransientModel):
    _name = 'school.bulk.attendance.line'
    _description = 'Bulk Attendance Line'

    wizard_id = fields.Many2one('school.bulk.attendance.wizard', ondelete='cascade')
    student_id = fields.Many2one('school.student', string='Student', required=True)
    status = fields.Selection([
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    ], string='Status', required=True, default='present')
