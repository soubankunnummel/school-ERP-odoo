# -*- coding: utf-8 -*-
"""
settings.py — School Configuration Settings
=============================================
Stores school-wide settings like min attendance %, discount threshold.
MERN equivalent: a config collection / .env values stored in DB.

Two models here:
  1. school.settings        — a singleton config record (simple key-value store)
  2. school.res.config       — extends Odoo's Settings UI
"""
from odoo import api, fields, models


class SchoolSettings(models.Model):
    """
    Singleton config model.
    MERN equivalent: a 'settings' collection with one document.
    """
    _name = 'school.settings'
    _description = 'School Settings'

    name = fields.Char(default='School Configuration', readonly=True)
    min_attendance_percentage = fields.Float(
        string='Minimum Attendance %',
        default=75.0,
        digits=(5, 2),
        help="Students below this attendance % will be flagged."
    )
    fee_discount_percentage = fields.Float(
        string='Fee Discount %',
        default=10.0,
        digits=(5, 2),
        help="Discount applied when student enrolls in more than threshold subjects."
    )
    discount_subject_threshold = fields.Integer(
        string='Discount Subject Threshold',
        default=5,
        help="Number of subjects after which fee discount applies."
    )
    school_name = fields.Char(string='School Name', default='Smart School ERP')
    academic_year = fields.Char(string='Current Academic Year', default='2024-25')
    auto_mark_absent = fields.Boolean(
        string='Auto-mark Absent',
        default=True,
        help="Cron job will auto-mark absent if no attendance entry found."
    )

    @api.model
    def get_settings(self):
        """Returns the singleton settings record (creates if not exists)."""
        settings = self.search([], limit=1)
        if not settings:
            settings = self.create({})
        return settings
