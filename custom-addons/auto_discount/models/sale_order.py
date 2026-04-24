# from odoo import models

# class SaleOrder(models.Model):
#     _inherit = 'sale.order'

#     def create(self, vals):
#         order = super().create(vals)

#         if order.amount_total > 5000:
#             for line in order.order_line:
#                 line.discount = 10

#         return order


#     def write(self, vals):
#         res = super().write(vals)
#         print("Write method called with vals:", res)
#         for order in self:
#             if order.amount_total > 5000:
#                 for line in order.order_line:
#                     line.discount = 10

#         return res


from odoo import models , api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('order_line')
    def _onchange_auto_discount(self):
            min_amount = float(self.env['ir.config_parameter'].sudo().get_param('auto_discount.min_amount', 0))
            percentage = float(self.env['ir.config_parameter'].sudo().get_param('auto_discount.percentage', 0))

            total = sum(line.price_unit * line.product_uom_qty for line in self.order_line)

            if total > min_amount:
                for line in self.order_line:
                    line.discount = percentage
                    
            else:
                for line in self.order_line:
                    line.discount = 0


    add = lambda a, b: a + b
    print(add(2, 3))  # Output: 5
    def create(self, vals):
        order = super().create(vals)

        min_amount = float(self.env['ir.config_parameter'].sudo().get_param('auto_discount.min_amount', 0))
        percentage = float(self.env['ir.config_parameter'].sudo().get_param('auto_discount.percentage', 0))

        if order.amount_total > min_amount:
            for line in order.order_line:
                line.discount = percentage

        return order


    def write(self, vals):
        res = super().write(vals)

        min_amount = float(self.env['ir.config_parameter'].sudo().get_param('auto_discount.min_amount', 0))
        percentage = float(self.env['ir.config_parameter'].sudo().get_param('auto_discount.percentage', 0))

        for order in self:
            if order.amount_total > min_amount:
                for line in order.order_line:
                    line.discount = percentage
                
                order.message_post(body=f"Auto discount of {percentage}% applied based on total amount exceeding {min_amount}.")
            else:
                for line in order.order_line:
                    line.discount = 0

                order.message_post(body=f"Auto discount removed as total amount is below {min_amount}.")

        return res