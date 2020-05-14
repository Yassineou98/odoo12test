from odoo import fields, models, api
from odoo.tools import safe_eval


class DepartmentService (models.Model):
    _name = 'department'
    _description = 'Department of Topnet'

    name = fields.Char(string='Department', required=True, translate=True)
    chef = fields.Many2one('res.users', string='Head of Department')

    service_ids = fields.One2many(comodel_name='service', inverse_name='department_ids', string='Services', required=False)
    dir_ids = fields.Many2one(comodel_name='dep_ids', string='Direction_ids', required=False)


