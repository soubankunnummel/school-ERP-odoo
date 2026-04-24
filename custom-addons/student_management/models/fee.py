# -*- coding: utf-8 -*-
"""
fee.py — Fee / Payment Model
==============================
MERN equivalent: Fee collection with student ref and payment status
Covers: computed discount, overdue logic, workflow
"""
from datetime import date
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Fee(models.Model):
    _name = 'school.fee'
    _description = 'Student Fee'
    _inherit = ['mail.thread']
    _order = 'due_date asc'

    name = fields.Char(string='Fee Reference', copy=False, readonly=True,
                       default='New')
    student_id = fields.Many2one('school.student', string='Student',
                                 required=True, ondelete='cascade', tracking=True)
    class_id = fields.Many2one('school.class', string='Class',
                               related='student_id.class_id', store=True, readonly=True)
    fee_type = fields.Selection([
        ('tuition', 'Tuition Fee'),
        ('exam', 'Exam Fee'),
        ('library', 'Library Fee'),
        ('sports', 'Sports Fee'),
        ('transport', 'Transport Fee'),
        ('other', 'Other'),
    ], string='Fee Type', required=True, default='tuition')

    amount = fields.Float(string='Original Amount', required=True, digits=(10, 2))
    discount_percent = fields.Float(string='Discount %', digits=(5, 2),
                                    compute='_compute_discount', store=True)
    discount_amount = fields.Float(string='Discount Amount', digits=(10, 2),
                                   compute='_compute_discount', store=True)
    final_amount = fields.Float(string='Final Amount', digits=(10, 2),
                                compute='_compute_discount', store=True)
    paid_amount = fields.Float(string='Paid Amount', digits=(10, 2))
    balance = fields.Float(string='Balance Due', compute='_compute_balance',
                           store=True, digits=(10, 2))

    due_date = fields.Date(string='Due Date', required=True)
    paid_date = fields.Date(string='Paid Date')
    is_overdue = fields.Boolean(string='Overdue', compute='_compute_overdue',
                                store=True)
    state = fields.Selection([
        ('pending', 'Pending'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('waived', 'Waived'),
    ], string='Status', default='pending', tracking=True)

    note = fields.Text(string='Notes')

    # ------------------------------------------------------------------ #
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'school.fee.sequence') or 'FEE/0001'
        return super().create(vals_list)

    # ------------------------------------------------------------------ #
    @api.depends('student_id', 'student_id.has_fee_discount', 'amount')
    def _compute_discount(self):
        """
        Smart discount: if student has >5 subjects, apply discount from settings.
        MERN: business rule computed in backend service.
        """
        settings = self.env['school.settings'].sudo().get_settings()
        discount_pct = settings.fee_discount_percentage if settings else 10.0

        for fee in self:
            if fee.student_id.has_fee_discount:
                fee.discount_percent = discount_pct
                fee.discount_amount = fee.amount * (discount_pct / 100)
            else:
                fee.discount_percent = 0.0
                fee.discount_amount = 0.0
            fee.final_amount = fee.amount - fee.discount_amount

    @api.depends('final_amount', 'paid_amount')
    def _compute_balance(self):
        for fee in self:
            fee.balance = fee.final_amount - fee.paid_amount

    @api.depends('due_date', 'state')
    def _compute_overdue(self):
        today = fields.Date.today()
        for fee in self:
            fee.is_overdue = (
                fee.state not in ('paid', 'waived') and
                fee.due_date and fee.due_date < today
            )

    # ------------------------------------------------------------------ #
    def action_mark_paid(self):
        for fee in self:
            fee.paid_amount = fee.final_amount
            fee.paid_date = fields.Date.today()
            fee.state = 'paid'
            fee.message_post(body="Fee marked as fully paid.")

    def action_waive(self):
        for fee in self:
            fee.state = 'waived'
            fee.message_post(body="Fee waived by admin.")

    # Scheduled action calls this (cron)
    @api.model
    def _mark_overdue_fees(self):
        """
        Cron job: auto-mark overdue fees.
        MERN equivalent: node-cron scheduled task.
        """
        today = fields.Date.today()
        overdue = self.search([
            ('due_date', '<', today),
            ('state', 'not in', ['paid', 'waived', 'overdue']),
        ])
        overdue.write({'state': 'overdue'})
        import logging
        logging.getLogger(__name__).info(
            f"Cron: Marked {len(overdue)} fees as overdue."
        )
