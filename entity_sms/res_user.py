# -*- coding: utf-8 -*-

from openerp.osv import fields, osv

class res_users(osv.Model):
    _inherit = 'res.users'
    _columns = {
        'default_sms_number': fields.many2one('esms.verified.numbers', 'Default SMS Number'),
    }

    def __init__(self, pool, cr):
        init_res = super(res_users, self).__init__(pool, cr)
        # duplicate list to avoid modifying the original reference
        self.SELF_WRITEABLE_FIELDS = list(self.SELF_WRITEABLE_FIELDS)
        self.SELF_WRITEABLE_FIELDS.extend(['default_sms_number'])
        return init_res
