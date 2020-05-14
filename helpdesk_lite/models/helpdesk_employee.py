from odoo import fields, models, api


class Employee (models.Model):
    _name = 'employee'
    _description = 'Employee of topnet'
    _inherit = 'hr.employee'

    name = fields.Char(string='Employee', required=False)


