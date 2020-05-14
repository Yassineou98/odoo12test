from odoo import fields, models, api
import base64
import logging
from odoo import tools, _
from odoo.exceptions import ValidationError, AccessError
from odoo.modules.module import get_module_resource
import re

_logger = logging.getLogger(__name__)

State = [
    ('user', 'User'),
    ('technical', 'Technical'),
    ('manager', 'Manager'),
    ('admin', 'Administration'),
]


class EmployeeHelpdesk(models.Model):
    _name = 'helpdesk_lite.employee'
    _description = 'Topnet employee'
    _inherit = ['resource.mixin']

    @api.model
    def _default_image(self):
        image_path = get_module_resource('helpdesk_lite', 'static/src/img', 'default_image.png')
        return tools.image_resize_image_big(base64.b64encode(open(image_path, 'rb').read()))

    # personal data
    name = fields.Char(string="Employee name", related='resource_id.name', oldname='name_related', require=True)
    address_id = fields.Many2one(comodel_name='res.partner', string='Company address', required=False, readonly=True,
                                 default=lambda self: self.env.user.company_id)
    work_phone = fields.Char(string="Phone", required=True)
    work_email = fields.Char(string="Email", required=True)
    work_stat = fields.Selection(selection=State, string="Work Place", required=True)

    # department
    department_ids = fields.Many2one(comodel_name='department', string='Department', required=True)
    team_ids = fields.Many2one(comodel_name='', string='Team_ids', required=False)
    # privilege
    user_id = fields.Many2one('res.users', 'User', related='resource_id.user_id', readonly=False)

    # image 64bit
    image = fields.Binary(
        "Photo", default=_default_image, attachment=True,
        help="This field holds the image used as photo for the employee, limited to 1024x1024px.")
    image_medium = fields.Binary(
        "Medium-sized photo", attachment=True,
        help="Medium-sized photo of the employee. It is automatically "
             "resized as a 128x128px image, with aspect ratio preserved. "
             "Use this field in form views or some kanban views.")
    image_small = fields.Binary(
        "Small-sized photo", attachment=True,
        help="Small-sized photo of the employee. It is automatically "
             "resized as a 64x64px image, with aspect ratio preserved. "
             "Use this field anywhere a small image is required.")

    # _sql_constraints = [
    #     ('work_email_unique', 'unique(work_email)', "work email already exists!")
    # ]

    @api.onchange('work_email')
    def validate_mail(self):
        if self.work_email:
            match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', self.work_email)
            if match == None:
                raise ValidationError('Not a valid E-mail ID')

    def _sync_user(self, user):
        vals = dict(
            name=user.name,
            image=user.image,
            work_email=user.email,
        )
        return vals

    @api.multi
    def unlink(self):
        resources = self.mapped('resource_id')
        super(EmployeeHelpdesk, self).unlink()
        return resources.unlink()

    @api.onchange('work_phone')
    def validate_telephone(self):
        if self.work_phone:
            match = re.match('^[0-9]\d{7}$', self.work_phone)
            if match == None:
                raise ValidationError('Not a valid phone number')

    @api.onchange('user_id')
    def _onchange_user(self):
        if self.user_id:
            self.update(self._sync_user(self.user_id))

    @api.model
    def create(self, vals):
        if vals.get('user_id'):
            vals.update(self._sync_user(self.env['res.users'].browse(vals['user_id'])))
        tools.image_resize_images(vals)
        employee = super(EmployeeHelpdesk, self).create(vals)
        return employee

    @api.multi
    def write(self, vals):
        if vals.get('user_id'):
            vals.update(self._sync_user(self.env['res.users'].browse(vals['user_id'])))
        tools.image_resize_images(vals)
        res = super(EmployeeHelpdesk, self).write(vals)
        return res
