from odoo import fields, models, api, _


class TicketReport (models.Model):
    _name = 'report.helpdesk_lite.ticket'
    _description = 'Ticket report'

    @api.model
    def _get_report_values(self, docids, data=None):
        tickets = self.env['helpdesk_lite.ticket'].search([])
        # if data['form']['patient_id']:
        #     appointments = self.env['hospital.appointment'].search([('patient_id', '=', data['form']['patient_id'][0])])
        # else:
        #     appointments = self.env['hospital.appointment'].search([])
        # appointment_list = []
        # for app in appointments:
        #     vals = {
        #         'name' # return {
        #         #     'doc_model': 'hospital.patient',
        #         #     'appointments': appointments,
        #         # }: app.name,
        #         'notes': app.notes,
        #         'appointment_date': app.appointment_date
        #     }
        #     appointment_list.append(vals)
        return {
            'doc_model': 'helpdesk_lite.ticket',
            'tickets': tickets,
        }



