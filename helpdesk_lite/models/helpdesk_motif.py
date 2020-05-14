# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
from .helpdesk_ticket import (AVAILABLE_PRIORITIES)


class Motif(models.Model):
    _name = "motifs"
    _description = "les motifs"

    name = fields.Char(
        string='Motif',
        required=True, translate=True)
    # category_ids = fields.Many2many(
    #   comodel_name='type',
    #  string='motifs')
    category_ids = fields.Many2one(
        comodel_name='type',
        string='Type',
        required=False)
    default_priority = fields.Selection(
        string='Priority',
        selection=AVAILABLE_PRIORITIES,
        default='3'
    )
    note_html = fields.Html(
        string='Note',
        translate=True,
    )
    sequence_id = fields.Many2one(
        'ir.sequence', 'Sequence', ondelete='restrict',
        help="Use this sequence to generate names for requests for this motif")
    ticket_ids = fields.One2many(
        'helpdesk_lite.ticket', 'motif_id', 'Tickets', readonly=True, copy=False)

    description = fields.Text(string='Description', translate=True)

    help_html = fields.Html(string='Help', translate=True)

    @api.model
    def create(self, vals):
        r_motif = super(Motif, self).create(vals)
        return r_motif