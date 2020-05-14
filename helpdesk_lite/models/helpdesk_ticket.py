# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, exceptions, SUPERUSER_ID, _
import re
from odoo.exceptions import AccessError

TRACK_FIELD_CHANGES = set((
    'stage_id', 'user_id', 'type_id', 'category_id', 'request_text',
    'partner_id', 'category_id', 'priority', 'impact', 'urgency'))
REQUEST_TEXT_SAMPLE_MAX_LINES = 3
KANBAN_READONLY_FIELDS = set(('type_id', 'category_id', 'stage_id'))
AVAILABLE_PRIORITIES = [
    ('0', 'Not set'),
    ('1', 'Very Low'),
    ('2', 'Low'),
    ('3', 'Medium'),
    ('4', 'High'),
    ('5', 'Urgent'),
]


class HelpdeskTicket(models.Model):
    _name = "helpdesk_lite.ticket"
    _description = "Helpdesk Tickets"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = "priority desc, create_date desc"
    _mail_post_access = 'read'

    @api.model
    def _get_default_stage_id(self):
        return self.env['helpdesk_lite.stage'].search([], order='sequence', limit=1)

    name = fields.Char(
        required=True, index=True, readonly=True, copy=False,
        default="New")

    # newticket = fields.Char(string='New',
    #                       required=True, index=True, readonly=True, default="New Ticket",
    #                      copy=False, track_visibility='always')
    description = fields.Html('Private Note', required=True)
    commercial_partner_id = fields.Many2one(
        related='partner_id.commercial_partner_id', string='Customer Company', store=True, index=True)
    contact_name = fields.Char('Contact Name')
    email_from = fields.Char('Email', help="Email address of the contact", index=True)

    # date
    created_by_id = fields.Many2one(
        'res.users', 'Created by', readonly=True, ondelete='restrict',
        default=lambda self: self.env.user,
        help="Request was created by this user", copy=False)
    date_created = fields.Datetime(
        'Created', default=fields.Datetime.now, readonly=True, copy=False)
    date_closed = fields.Datetime('Closed', readonly=True, copy=False)
    date_assigned = fields.Datetime('Assigned', readonly=True, copy=False)

    date_moved = fields.Datetime('Moved', readonly=True, copy=False)
    moved_by_id = fields.Many2one(
        'res.users', 'Moved by', readonly=True, ondelete='restrict',
        copy=False)

    author_id = fields.Many2one(
        'res.users', 'Author', readonly=True, ondelete='restrict',
        default=lambda self: self.env.user,
        help="Request was created by this user", copy=False)
    partner_id = fields.Many2one(
        'res.partner', 'Partner', readonly=True, index=True, required=True,
        ondelete='restrict',
        track_visibility='onchange',
        domain=[('is_company', '=', False)],
        default=lambda self: self.env.user.partner_id,
        help="Author of this request")

    # user_id = fields.Many2one('res.users', string='Assigned to', track_visibility='onchange', index=True, default=False,
    #                           readonly=True)
    user_id = fields.Many2one(
        'res.users', 'Assigned to',
        ondelete='restrict', track_visibility='onchange', readonly=True,
        help="User responsible for next action on this request.")

    team_id = fields.Many2one('helpdesk_lite.team', string='Support Team', track_visibility='onchange',
                              default=lambda self: self.env['helpdesk_lite.team'].sudo()._get_default_team_id(
                                  user_id=self.env.uid),
                              index=True,
                              help='When sending mails, the default email address is taken from the support team.')
    date_deadline = fields.Datetime(string='Deadline', track_visibility='onchange')
    date_done = fields.Datetime(string='Done', track_visibility='onchange')
    type_id = fields.Many2one(
        'type', 'Type', index=True,
        required=False, ondelete="restrict", track_visibility='onchange',
        help="Category of request")
    motif_id = fields.Many2one(
        'motifs', 'Motif', ondelete='restrict',
        required=True, index=True, track_visibility='always',
        help="Type of request")
    stage_id = fields.Many2one('helpdesk_lite.stage', string='Stage', index=True, track_visibility='onchange',
                               domain="[]",
                               copy=False,
                               group_expand='_read_group_stage_ids',
                               default=_get_default_stage_id)
    last = fields.Boolean(related='stage_id.last', index=True, readonly=True)

    priority = fields.Selection(AVAILABLE_PRIORITIES, 'Priority', index=True, default='3', track_visibility='onchange',
                                related='motif_id.default_priority')
    kanban_state = fields.Selection([('normal', 'Normal'), ('blocked', 'Blocked'), ('done', 'Ready for next stage')],
                                    string='Kanban State', track_visibility='onchange',
                                    required=True, default='normal',
                                    help="""A Ticket's kanban state indicates special situations affecting it:\n
                                           * Normal is the default situation\n
                                           * Blocked indicates something is preventing the progress of this ticket\n
                                           * Ready for next stage indicates the ticket is ready to go to next stage""")
    attachment_ids = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'helpdesk_lite.ticket')],
                                     string="Media Attachments")
    color = fields.Integer('Color Index')
    legend_blocked = fields.Char(related="stage_id.legend_blocked", readonly=True)
    legend_done = fields.Char(related="stage_id.legend_done", readonly=True)
    legend_normal = fields.Char(related="stage_id.legend_normal", readonly=True)

    description_motif = fields.Text(related='motif_id.description',
                                    readonly=True)
    note_html = fields.Html(related='motif_id.note_html',
                            readonly=True)

    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)

    can_change_category = fields.Boolean(
        compute='_compute_can_change_category', readonly=True)
    is_new_request = fields.Integer(
        compute='_compute_is_new_request', readonly=True,
        default=1)

    closed_by_id = fields.Many2one(
        'res.users', 'Closed by', readonly=True, ondelete='restrict',
        copy=False, help="Request was closed by this user")

    can_change_assignee = fields.Boolean(
        compute='_compute_can_change_assignee', readonly=True)

    def _hook_can_change_assignee(self):
        """ Can be overridden in other addons
        """
        self.ensure_one()
        return not self.last

    @api.depends('motif_id', 'stage_id', 'user_id',
                 'partner_id', 'created_by_id')
    def _compute_can_change_assignee(self):
        for rec in self:
            rec.can_change_assignee = rec._hook_can_change_assignee()

    # remplacé par le related user
    # @api.depends()
    # def _create_update_from_motif(self, r_motif, vals):
    #     vals['priority'] = r_motif.sudo().default_priority
    #
    # @api.onchange('motif_id')
    # def onchange_type_id(self):
    #     # Set default priority
    #     for ticket in self:
    #         ticket.priority = ticket.motif_id.default_priority

    @api.depends()
    def _compute_is_new_request(self):
        for record in self:
            record.is_new_request = int(not bool(record.id))

    is_new_request = fields.Integer(
        compute='_compute_is_new_request', readonly=True,
        default=1)

    @api.depends()
    def _hook_can_change_category(self):
        self.ensure_one()
        return self.stage_id == self.sudo().type_id.start_stage_id

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """ This function sets partner email address based on partner
        """
        self.email_from = self.partner_id.email

    @api.multi
    def copy(self, default=None):
        if default is None:
            default = {}
        default.update(name=_('%s (copy)') % (self.name))
        return super(HelpdeskTicket, self).copy(default=default)

    def _can_add__recipient(self, partner_id):
        if not self.partner_id.email:
            return False
        if self.partner_id in self.message_follower_ids.mapped('partner_id'):
            return False
        return True

    @api.multi
    def message_get_suggested_recipients(self):
        recipients = super(HelpdeskTicket, self).message_get_suggested_recipients()
        try:
            for tic in self:
                if tic.partner_id:
                    if tic._can_add__recipient(tic.partner_id):
                        tic._message_add_suggested_recipient(recipients, partner=tic.partner_id,
                                                             reason=_('Customer'))
                elif tic.email_from:
                    tic._message_add_suggested_recipient(recipients, email=tic.email_from,
                                                         reason=_('Customer Email'))
        except AccessError:  # no read access rights -> just ignore suggested recipients because this imply modifying followers
            pass
        return recipients

    def _email_parse(self, email):
        match = re.match(r"(.*) *<(.*)>", email)
        if match:
            contact_name, email_from = match.group(1, 2)
        else:
            match = re.match(r"(.*)@.*", email)
            contact_name = match.group(1)
            email_from = email
        return contact_name, email_from

    @api.model
    def message_new(self, msg, custom_values=None):
        match = re.match(r"(.*) *<(.*)>", msg.get('from'))
        if match:
            contact_name, email_from = match.group(1, 2)
        else:
            match = re.match(r"(.*)@.*", msg.get('from'))
            contact_name = match.group(1)
            email_from = msg.get('from')

        body = tools.html2plaintext(msg.get('body'))
        bre = re.match(r"(.*)^-- *$", body, re.MULTILINE | re.DOTALL | re.UNICODE)
        desc = bre.group(1) if bre else None

        defaults = {
            'name': msg.get('subject') or _("No Subject"),
            'email_from': email_from,
            'description': desc or body,
        }

        partner = self.env['res.partner'].sudo().search([('email', '=ilike', email_from)], limit=1)
        if partner:
            defaults.update({
                'partner_id': partner.id,
            })
        else:
            defaults.update({
                'contact_name': contact_name,
            })

        create_context = dict(self.env.context or {})
        # create_context['default_user_id'] = False
        # create_context.update({
        #     'mail_create_nolog': True,
        # })

        company_id = False
        if custom_values:
            defaults.update(custom_values)
            team_id = custom_values.get('team_id')
            if team_id:
                team = self.env['helpdesk_lite.team'].sudo().browse(team_id)
                if team.company_id:
                    company_id = team.company_id.id
        if not company_id and partner.company_id:
            company_id = partner.company_id.id
        defaults.update({'company_id': company_id})

        return super(HelpdeskTicket, self.with_context(create_context)).message_new(msg, custom_values=defaults)

    @api.model_create_single
    def create(self, vals):
        context = dict(self.env.context)
        context.update({
            'mail_create_nosubscribe': False,
        })

        vals['name'] = self.env['ir.sequence'].sudo().next_by_code('helpdesk_lite.ticket.name')
        res = super(HelpdeskTicket, self.with_context(context)).create(vals)
        # res = super().create(vals)
        if res.partner_id:
            res.message_subscribe([res.partner_id.id])

        return res

    @api.multi
    def write(self, vals):
        # stage change: update date_last_stage_update
        if 'stage_id' in vals:
            if 'kanban_state' not in vals:
                vals['kanban_state'] = 'normal'

        if vals.get('stage_id'):
            vals.update({'date_moved': fields.Datetime.now()})
            vals['moved_by_id'] = self.env.user.id

        if vals.get('user_id'):
            vals.update({
                'date_assigned': fields.Datetime.now(),
            })

        if self.stage_id.last:
            vals.update({'date_done': fields.Datetime.now()})
            vals['closed_by_id'] = self.env.user.id
        else:
            vals.update({'date_done': False})
            vals['closed_by_id'] = False

        # self.ensure_ticket_done(vals)
        return super(HelpdeskTicket, self).write(vals)

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):

        search_domain = []

        # perform search
        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    @api.multi
    def takeit(self):
        self.ensure_one()
        self.ensure_can_assign()
        vals = {
            'user_id': self.env.uid,
            'date_assigned': fields.Datetime.now(),
            # 'team_id': self.env['helpdesk_lite.team'].sudo()._get_default_team_id(user_id=self.env.uid).id
        }
        return super(HelpdeskTicket, self).write(vals)

    @api.multi
    def assignto(self):
        self.ensure_one()
        self.ensure_can_assign()
        action = self.env.ref('helpdesk_lite.action_helpdesk_wizard_assign')
        action = action.read()[0]
        action['context'] = {
            'default_ticket_id': self.id,
        }
        return action

    # def ensure_ticket_done(self, vals):
    #     self.ensure_one()
    #     if self.last:
    #         vals.update({'date_done': fields.Datetime.now()})
    #         vals['closed_by_id'] = self.env.user.id
    #     else:
    #         vals.update({'date_done': False})
    #         vals['closed_by_id'] = False
    #     return vals

    

    def ensure_can_assign(self):
        self.ensure_one()
        if self.last:
            raise exceptions.UserError(_(
                "You can not assign this request (%s), "
                "because this request is closed."
            ) % self.display_name)
        if not self.can_change_assignee:
            raise exceptions.UserError(_(
                "You can not assign this (%s) request"
            ) % self.display_name)

    @api.model_cr
    def _register_hook(self):
        HelpdeskTicket.website_form = bool(self.env['ir.module.module'].
                                           search([('name', '=', 'website_form'), ('state', '=', 'installed')]))
        if HelpdeskTicket.website_form:
            self.env['ir.model'].search([('model', '=', self._name)]).write({'website_form_access': True})
            self.env['ir.model.fields'].formbuilder_whitelist(
                self._name, ['name', 'description', 'date_deadline', 'priority', 'partner_id', 'user_id'])
        pass

    # def _preprocess_write_changes(self, changes):
    #     vals = super(HelpdeskTicket, self)._preprocess_write_changes(changes)
    #
    #     if 'user_id' in changes:
    #         new_user = changes['user_id'][1]  # (old_user, new_user)
    #         if new_user:
    #             vals['date_assigned'] = fields.Datetime.now()
    #         else:
    #             vals['date_assigned'] = False
    #
    #     if 'stage_id' in changes:
    #         # old_stage, new_stage = changes['stage_id']
    #         # route = Route.ensure_route(self, new_stage.id)
    #         # route.hook_before_stage_change(self)
    #         # vals['last_route_id'] = route.id
    #         vals['date_moved'] = fields.Datetime.now()
    #         vals['moved_by_id'] = self.env.user.id
    #
    #         # if not old_stage.closed and new_stage.closed:
    #         #     vals['date_closed'] = fields.Datetime.now()
    #         #     vals['closed_by_id'] = self.env.user.id
    #         # elif old_stage.closed and not new_stage.closed:
    #         #     vals['date_closed'] = False
    #         #     vals['closed_by_id'] = False
    #
    #     # if 'type_id' in changes:
    #     #     raise exceptions.ValidationError(_(
    #     #         'It is not allowed to change request type'))
    #     if 'description' in changes:
    #         raise exceptions.ValidationError(_(
    #             'It is not allowed to change ticket description'))
    #     return vals
