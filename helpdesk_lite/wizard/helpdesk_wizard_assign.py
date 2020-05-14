from odoo import fields, api, models


class HelpdeskWizardAssign(models.TransientModel):
    _name = "assign"
    _description = "Helpdesk assign"

    def _default_user_id(self):
        return self.env.user

    ticket_id = fields.Many2one('helpdesk_lite.ticket', 'Ticket', requeired=True)
    user_id = fields.Many2one(
        'res.users', string="User", default=_default_user_id, required=True)
    partner_id = fields.Many2one(
        'res.partner', related="user_id.partner_id",
        readonly=True, store=False)
    comment = fields.Text()

    def do_assign(self):
        for rec in self:
            rec.ticket_id.ensure_can_assign()
            rec.ticket_id.user_id = rec.user_id
            if rec.comment:
                rec.ticket_id.message_post(body=rec.comment)