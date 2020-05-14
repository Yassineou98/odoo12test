from odoo import fields, models, api


class ServiceDepartment(models.Model):
    _name = 'service'
    _description = 'Service of Topnet'

    name = fields.Char(string='Service', required=False)
    department_ids = fields.Many2one(comodel_name='department', string='Department', required=False)
    id = fields.Integer(string="Service Number", required=False)
    group_id = fields.One2many(
        comodel_name='helpdesk_lite.team',
        inverse_name='service_id',
        string='Group',
        required=False)
