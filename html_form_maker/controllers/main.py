import openerp.http as http
from openerp.http import request
import logging
_logger = logging.getLogger(__name__)
import werkzeug
import base64
import json

class HtmlFormController(http.Controller):

    @http.route('/form/thankyou', type="http", auth="public", website=True)
    def ehtml_thanks(self, **kw):
        return http.request.render('html_form_maker.html_thank_you', {})

    @http.route('/form/deletefield', website=True, type='json', auth="user")
    def html_delete_field(self, **kw):

        values = {}
	for field_name, field_value in kw.items():
            values[field_name] = field_value
        
        request.env['html.form.field'].unlink(values['html_field_id'])


    @http.route('/form/updateform', website=True, type='json', auth="user")
    def html_update_form(self, **kw):

        values = {}
	for field_name, field_value in kw.items():
            values[field_name] = field_value

        model_id = request.env['ir.model'].search([('model','=', values['model_id'] )])[0]

        if int(values['form_id']) == 0:
            #create the form
            my_form = request.env['html.form'].create({'name':values['name'], 'return_url': values['return_url'], 'model_id': model_id.id })
            return my_form.id
        
        return "0"

    @http.route('/form/updatefield', website=True, type='json', auth="user")
    def ehtml_update_field(self, **kw):

        values = {}
	for field_name, field_value in kw.items():
            values[field_name] = field_value
        

        if int(values['html_field_id']) == 0:
            #create the field
            my_field = request.env['html.form.field'].create({'html_id':values['form_id'], 'field_id': values['field'], 'field_type': values['field_type'], 'html_name': values['html_name'], 'field_label': values['label'] })
            
            method = '_generate_html_%s' % (values['field_type'],)
            action = getattr(self, method, None)
        
            if not action:
	        raise NotImplementedError('Method %r is not implemented on %r object.' % (method, self))

            return {'field_id': my_field.id, 'html': action(my_field)}
            
            
        return "0"

    def _generate_html_textbox(self, field):
        """Generate textbox HTML"""
        html_output = ""        
        html_output += "<div class=\"form-group\">\n"
	html_output += "  <label class=\"control-label\" for=\"" + field.html_name.encode("utf-8") + "\""
		    		
	if field.field_id.required == False:
	    html_output += " style=\"font-weight: normal\""
		    		
	html_output += ">" + field.field_label + "</label>\n"	    
	html_output += "  <input type=\"text\" class=\"form-control\" name=\"" + field.html_name.encode("utf-8") + "\""
		                                    
	if field.field_id.required == True:
	    html_output += " required"
	
	html_output += "/>\n"
	html_output += "</div>\n"
	
	return html_output

    def _generate_html_textarea(self, field):
        """Generate textarea HTML"""
        html_output = ""
        html_output += "<div class=\"form-group\">\n"
	html_output += "  <label class=\"control-label\" for=\"" + field.html_name.encode("utf-8") + "\""
		    		
	if field.field_id.required == False:
	    html_output += " style=\"font-weight: normal\""
		    		
	html_output += ">" + field.field_label + "</label>\n"	    
	html_output += "  <textarea class=\"form-control\" name=\"" + field.html_name.encode("utf-8") + "\""
		                                    
	if field.field_id.required == True:
	    html_output += " required"
	
	html_output += "/>\n"
	html_output += "</div>\n"
	
	return html_output

    def _generate_html_dropbox(self, field):
        """Generates a dropbox"""
        html_output = ""
        
        if field.field_id.ttype == "selection":
            html_output += "<div class=\"form-group\">\n"
	    html_output += "  <label class=\"control-label\" for=\"" + field.html_name.encode("utf-8") + "\""
		                
            if field.field_id.required == False:
                html_output += " style=\"font-weight: normal\""                
                		
            html_output += ">" + field.field_label
            html_output += "</label>\n"
	    html_output += "  <select class=\"form-control\" name=\"" + field.html_name.encode("utf-8") + "\""
                		    
	    if field.field_id.required == True:
	        html_output += " required"
	        
    	    html_output += ">\n"
    	    html_output += "    <option value=\"\">Select Option</option>\n"
    
    	    selection_list = dict(request.env[field.field_id.model_id.model]._columns[field.field_id.name].selection)
    	        
    	    for selection_value,selection_label in selection_list.items():
    	        html_output += "    <option value=\"" + selection_value.encode("utf-8") + "\">" + selection_label.encode("utf-8") + "</option>\n"
    	        
    	    html_output += "  </select>\n"
    	    html_output += "</div>\n"
    	    
    	    return html_output
    
    @http.route('/form/getfields', website=True, type='http', auth="public")
    def ehtml_get_fields(self, **kw):

        values = {}
	for field_name, field_value in kw.items():
            values[field_name] = field_value        
        
        my_return = []
        #valid_data_types = request.env['html.form.field.type'].sudo().search([('html_type','=','textbox')])
        my_fields = request.env['ir.model.fields'].search([('model_id.model','=','res.partner'), ('field_description','=ilike',"%" + values['term'] + "%")], limit=5)
        
        for my_field in my_fields:
            return_item = {"label": my_field.field_description + "(" + my_field.name + ")","description": my_field.field_description, "value": my_field.name, "id": my_field.id}
            my_return.append(return_item)
        
        
        return json.JSONEncoder().encode(my_return)

                
    @http.route('/form/insert',type="http", auth="public")
    def my_insert(self, **kwargs):
        
        values = {}
	for field_name, field_value in kwargs.items():
            values[field_name] = field_value
        
        #the referral string is what the campaign looks for
        secure_values = {}
        history_values = {}
        
        ref_url = http.request.httprequest.headers['Referer']
        
        entity_form = http.request.env['html.form'].sudo().browse(int(values['form_id']))
        
        new_history = http.request.env['html.form.history'].sudo().create({'ref_url':ref_url, 'html_id': entity_form.id})
        
        #populate an array which has ONLY the fields that are in the form (prevent injection)
        for fi in entity_form.fields_ids:
            if fi.field_id.ttype == "binary":
                secure_values[fi.field_id.name] = base64.encodestring(values[fi.html_name].read() )    
            else:
                secure_values[fi.field_id.name] = values[fi.html_name]
                
            new_history.insert_data.sudo().create({'html_id': new_history.id, 'field_id':fi.field_id.id, 'insert_value':values[fi.html_name]})

        #default values
        for df in entity_form.defaults_values:
            secure_values[df.field_id.name] = df.default_value
            new_history.insert_data.sudo().create({'html_id': new_history.id, 'field_id':df.field_id.id, 'insert_value':df.default_value})
        
        new_record = http.request.env[entity_form.model_id.model].sudo().create(secure_values)
        new_history.record_id = entity_form.id
        
        return werkzeug.utils.redirect(entity_form.return_url)