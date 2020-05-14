from odoo import fields, models, api


class Direction (models.Model):
    _name = 'direction'
    _description = 'Topnet Direction'

    name = fields.Char(string="Direction", required=True, Translate=True)
    dep_ids = fields.One2many(comodel_name='department', inverse_name='dir_ids', string='Department', required=False)
    


