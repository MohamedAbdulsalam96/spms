# Copyright (c) 2022, aoai and contributors
# For license information, please see license.txt

import frappe
from frappe.website.website_generator import WebsiteGenerator
from spms.methods.utils import generate_qrcode
from frappe.utils import cstr
from spms.methods.utils import update_sales_person
import hashlib
from frappe import _

class PaymentCollection(WebsiteGenerator):
	def validate(self):
		total_paid = self.total_paid
		total_allocated = 0
  
		for inv in self.invoices:
			if(inv.allocated == 0 or inv.allocated == None):
				frappe.throw(_(f'invoice {inv.invoice_no} has allocated value of 0'))
    
			total_allocated += inv.allocated
		if(total_paid != None):
			if total_allocated>total_paid:
				frappe.throw(_('The total allocated is more than the total paid.'))

	def on_submit(self) -> None:
		"""
		`update_collects_goal(self, 1)`
		
		This function is called when the user clicks the submit button. It updates the goal for the
		number of collects
		"""
		update_sales_person(self, 1)

	def on_cancel(self) -> None:
		"""
		`update_collects_goal(self, -1)`
		
		This function is called when the user clicks the "Cancel" button
		"""
		update_sales_person(self, -1)

	def before_submit(self):
		"""
		It takes the name of the route and generates a QR code image for it
		"""
		if not self.image:
			self.route = hashlib.sha1(str(self.name).encode()).hexdigest()
			site_name = cstr(frappe.local.site)
			image_path = generate_qrcode(
				site_name=site_name, route_name=self.route)
			self.image = image_path

	def before_save(self):

		if(self.total_paid != None):
			init_amount = self.initial_amount
			max_discount = frappe.db.get_single_value('SPMS Settings', 'max_discount_on_collecting')
			discount_value = 0
			if self.discount_type == "Percentage":
				discount_value = init_amount * (self.discount_percentage / 100)
			else:
				discount_value = self.discount

			if discount_value < max_discount or max_discount == 0:
				self.amount = init_amount - discount_value
				self.discount_amount = discount_value
			else:
				frappe.throw(_('The discount must be less than {0}%').format(max_discount))

		if(self.discount_amount != None):
			self.amount = self.initial_amount - self.discount_amount
		else:
			self.amount = self.initial_amount

		total_allocated = 0
		for i in self.invoices:
			total_allocated += i.allocated
   
		total_unallocated = self.total_paid-total_allocated
		self.total_unallocated = total_unallocated
