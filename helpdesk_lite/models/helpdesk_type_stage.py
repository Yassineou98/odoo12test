from odoo import api, fields, models, tools


class TypeStage(models.Model):
    _name = "type"
    _description = "les types"

    name = fields.Char(string='Type', required=True, translate=True)
    # request_type_ids = fields.Many2many(
    #    comodel_name='motifs',
    #   string='Request_type_ids')
    request_type_ids = fields.One2many(
        comodel_name='motifs',
        inverse_name='category_ids',
        string='Motifs',
    )
    color = fields.Integer('Color Index')
    description = fields.Text(translate=True)
    sequence = fields.Integer(index=True, default=5)
    code = fields.Char(required="True")