from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    discount_min_amount = fields.Float(string="Minimum Amount")
    discount_percentage = fields.Float(string="Discount Percentage")

    def set_values(self):
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_param('auto_discount.min_amount', self.discount_min_amount)
        self.env['ir.config_parameter'].sudo().set_param('auto_discount.percentage', self.discount_percentage)

    def get_values(self):
        res = super().get_values()
        res.update(
            discount_min_amount=float(self.env['ir.config_parameter'].sudo().get_param('auto_discount.min_amount', default=0)),
            discount_percentage=float(self.env['ir.config_parameter'].sudo().get_param('auto_discount.percentage', default=0)),
        )
        return res