from openerp import models, fields, api
import logging
from tempfile import TemporaryFile, NamedTemporaryFile
import zipfile
import base64
_logger = logging.getLogger(__name__)
from StringIO import StringIO
import os

class crm_migrate_image_wizard(models.TransientModel):

    _name = "crm.migrate.image.wizard"

    data = fields.Binary('Upload Image Zip')
    map_field = fields.Many2one('ir.model.fields', domain="[('model_id.model','=','res.partner')]", string='Mapping Field', required='True')
    filename = fields.Char()

    @api.one
    def import_images(self):
        
        error_string = ""
        myzipfile = zipfile.ZipFile(StringIO(base64.decodestring(self.data)))
        for name in myzipfile.namelist():
            zippy = myzipfile.open(name)
            image_string = zippy.read()
            my_partner = self.env['res.partner'].search([[self.map_field.name,'=',os.path.splitext(name)[0]]])
            if len(my_partner) == 1:
                my_partner.image = base64.b64encode(image_string)
            elif len(my_partner) > 1:
                #more then one Partner with identifer
                error_string += "more then one partner with ID (" + os.path.splitext(name)[0] + ")\n"
            else:
                #customer does not exist
                error_string += "Partner with ID (" + os.path.splitext(name)[0] + ") does not exist\n"
        
        self.env['crm.migrate.image'].create({'map_field':self.map_field.id,'error_text':error_string})
                
    
class crm_migrate_image(models.Model):

    _name = "crm.migrate.image"

    map_field = fields.Many2one('ir.model.fields', domain="[('model_id.model','=','res.partner')]", string='Mapping Field', readonly='True')
    filename = fields.Char()
    error_text = fields.Text()
    