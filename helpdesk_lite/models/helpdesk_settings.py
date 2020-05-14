import logging

_logger = logging.getLogger(__name__)
import requests
from odoo.http import request
import odoo
from odoo import api, fields, models


class HelpdeskSettings(models.Model):
    _name = "settings"
    _inherit = 'res.config.settings'

    allow_user_signup = fields.Boolean(string="Allow User Signup")

    @api.multi
    def set_values(self):
        super(HelpdeskSettings, self).set_values()
        self.env['ir.default'].set('helpdesk.settings', 'allow_user_signup', self.allow_user_signup)

    @api.model
    def get_values(self):
        res = super(WebsiteSupportSettings, self).get_values()
        res.update(
            allow_user_signup=self.env['ir.default'].get('helpdesk.settings', 'allow_user_signup'),
        )
        return res
