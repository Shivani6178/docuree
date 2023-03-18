from django.shortcuts import render
from django.urls import reverse
from django.shortcuts import render, HttpResponseRedirect, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import random
import string
from .models import Payment
from hospital.models import Patient
from pharmacy.models import Order, Cart
from doctor.models import Appointment, Prescription, Prescription_test, testCart, testOrder 
from django.contrib.auth.decorators import login_required


from django.core.mail import BadHeaderError, send_mail
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.utils.html import strip_tags
from django.conf import settings
import stripe
# This is your test secret API key.
stripe.api_key = settings.STRIPE_SECRET_KEY

# Create your views here.

def generate_random_string():
    N = 8
    string_var = ""
    string_var = ''.join(random.choices(
        string.ascii_uppercase + string.digits, k=N))
    string_var = "SSLCZ_TEST_" + string_var
    return string_var

def generate_random_invoice():
    N = 4
    string_var = ""
    string_var = ''.join(random.choices(string.digits, k=N))
    string_var = "#INV-" + string_var
    return string_var


def generate_random_val_id():
    N = 12
    string_var = ""
    string_var = ''.join(random.choices(
        string.ascii_uppercase + string.digits, k=N))
    return string_var


def payment_home(request):
    return render(request, 'index.html')

# @login_required


@csrf_exempt
def ssl_payment_request(request, pk, id):
    # Payment Request for appointment payment
    
    patient = Patient.objects.get(patient_id=pk)
    appointment = Appointment.objects.get(id=id)
    
    invoice_number = generate_random_invoice()
    
    post_body = {}
    post_body['total_amount'] = appointment.doctor.consultation_fee + appointment.doctor.report_fee
    post_body['currency'] = "INR"
    post_body['tran_id'] = generate_random_string()

    post_body['emi_option'] = 0
  
    post_body['cus_name'] = patient.username
    post_body['cus_email'] = patient.email
    post_body['cus_phone'] = patient.phone_number
    post_body['cus_add1'] = patient.address
    post_body['cus_city'] = "Mumbai"
    post_body['cus_country'] = "India"
    post_body['shipping_method'] = "NO"
    post_body['num_of_item'] = 1
    post_body['product_name'] = "Test"
    post_body['product_category'] = "Test Category"
    post_body['product_profile'] = "general"

    # Save in database
    appointment.transaction_id = post_body['tran_id']
    appointment.payment_status = "VALID"
    appointment.save()
    
    payment = Payment()
    payment.patient = patient
    payment.appointment = appointment
    payment.name = post_body['cus_name']
    payment.email = post_body['cus_email']
    payment.phone = post_body['cus_phone']
    payment.address = post_body['cus_add1']
    payment.city = post_body['cus_city']
    payment.country = post_body['cus_country']
    payment.transaction_id = post_body['tran_id']
    
    payment.consulation_fee = appointment.doctor.consultation_fee
    payment.report_fee = appointment.doctor.report_fee
    payment.invoice_number = invoice_number
    
    payment_type = "appointment"
    payment.payment_type = payment_type
    payment.status = "Done"
    payment.currency_amount = post_body['total_amount']
    payment.save()
    
    # Mailtrap
    patient_email = payment.patient.email
    patient_name = payment.patient.name
    patient_username = payment.patient.username
    patient_phone_number = payment.patient.phone_number
    doctor_name = appointment.doctor.name

    subject = "Payment Receipt for appointment"
    
    values = {
            "email":patient_email,
            "name":patient_name,
            "username":patient_username,
            "phone_number":patient_phone_number,
            "doctor_name":doctor_name,
            "tran_id":post_body['tran_id'],
            "currency_amount":post_body['total_amount'],        
        }
    
    html_message = render_to_string('appointment_mail_payment_template.html', {'values': values})
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(subject, plain_message, 'hospital_admin@gmail.com',  [patient_email], html_message=html_message, fail_silently=False)
    except BadHeaderError:
        return HttpResponse('Invalid header found')

    final_amount = (int(float(post_body['total_amount'])))*100
    
    YOUR_DOMAIN = 'http://127.0.0.1:8000/sslcommerz/ssl-payment-request/'
    checkout_session = stripe.checkout.Session.create(
        line_items=[
            {
                'price_data':{
                    'currency': 'inr',
                    'unit_amount': final_amount,
                    'product_data':{
                        'name': 'Appointment Payment',
                    },
                }, 
                'quantity': 1,
            },
        ],
        mode='payment',
        success_url=YOUR_DOMAIN + 'ssl-payment-success' + '/',
        cancel_url=YOUR_DOMAIN + 'ssl-payment-cancel' + '/',
    )
    
    return redirect(checkout_session.url, code=303)


@csrf_exempt
def ssl_payment_request_medicine(request, pk, id):
    # Payment Request for appointment payment
    
    patient = Patient.objects.get(patient_id=pk)
    order = Order.objects.get(id=id)
    
    invoice_number = generate_random_invoice()
    
    post_body = {}
    post_body['total_amount'] = order.final_bill()
    post_body['currency'] = "INR"
    post_body['tran_id'] = generate_random_string()

    post_body['emi_option'] = 0
  
    post_body['cus_name'] = patient.username
    post_body['cus_email'] = patient.email
    post_body['cus_phone'] = patient.phone_number
    post_body['cus_add1'] = patient.address
    post_body['cus_city'] = "mumbai"
    post_body['cus_country'] = "India"
    post_body['shipping_method'] = "NO"
    post_body['num_of_item'] = 1
    post_body['product_name'] = "Test"
    post_body['product_category'] = "Test Category"
    post_body['product_profile'] = "general"

    # Save in database
    order.trans_ID = post_body['tran_id']
    order.payment_status = "VALID"
    order.save()
    
    payment = Payment()
    payment.patient = patient
    payment.name = post_body['cus_name']
    payment.email = post_body['cus_email']
    payment.phone = post_body['cus_phone']
    payment.address = post_body['cus_add1']
    payment.city = post_body['cus_city']
    payment.country = post_body['cus_country']
    payment.transaction_id = post_body['tran_id']
    
    payment.invoice_number = invoice_number
    
    payment_type = "pharmacy"
    payment.payment_type = payment_type
    payment.status = "Done"
    payment.currency_amount = post_body['total_amount']
    payment.save()
    
    # Mailtrap
    patient_email = payment.patient.email
    patient_name = payment.patient.name
    patient_username = payment.patient.username
    patient_phone_number = payment.patient.phone_number
    
    ob = Cart.objects.filter(order__trans_ID=payment.transaction_id)
    len_ob = len(ob)
    
    order_cart = []   
    for i in range(len_ob):
        order_cart.append(ob[i])
    
    subject = "Payment Receipt for pharmacy"
    
    values = {
            "email":patient_email,
            "name":patient_name,
            "username":patient_username,
            "phone_number":patient_phone_number,
            "tran_id":post_body['tran_id'],
            "currency_amount":post_body['total_amount'],
            "order_cart":order_cart,
        }
    
    html_message = render_to_string('pharmacy_mail_payment_template.html', {'values': values})
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(subject, plain_message, 'hospital_admin@gmail.com',  [patient_email], html_message=html_message, fail_silently=False)
    except BadHeaderError:
        return HttpResponse('Invalid header found')
    
    # Reset cart
    Cart.objects.all().delete()
    
    final_amount = (int(float(post_body['total_amount'])))*100
    
    YOUR_DOMAIN = 'http://127.0.0.1:8000/sslcommerz/ssl-payment-request/'
    checkout_session = stripe.checkout.Session.create(
        line_items=[
            {
                # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                # TODO - replace hardcoded value of product price id to dynamic 
                'price_data':{
                    'currency': 'INR',
                    'unit_amount': final_amount,
                    'product_data':{
                        'name': 'medicine',
                    },
                }, 
                'quantity': 1,
            },
        ],
        mode='payment',
        success_url=YOUR_DOMAIN + 'ssl-payment-success' + '/',
        cancel_url=YOUR_DOMAIN + 'ssl-payment-cancel' + '/',
    )
    
    return redirect(checkout_session.url, code=303)


@csrf_exempt
def ssl_payment_request_test(request, pk, id, pk2):
    # Payment Request for test payment
    
    patient = Patient.objects.get(patient_id=pk)
    test_order = testOrder.objects.get(id=id)
    prescription = Prescription.objects.get(prescription_id=pk2)
    
    invoice_number = generate_random_invoice()
    
    post_body = {}
    post_body['total_amount'] = test_order.final_bill()
    post_body['currency'] = "BDT"
    post_body['tran_id'] = generate_random_string()
    
    post_body['emi_option'] = 0
  
    post_body['cus_name'] = patient.username
    post_body['cus_email'] = patient.email
    post_body['cus_phone'] = patient.phone_number
    post_body['cus_add1'] = patient.address
    post_body['cus_city'] = "Mumbai"
    post_body['cus_country'] = "India"
    post_body['shipping_method'] = "NO"
    post_body['num_of_item'] = 1
    post_body['product_name'] = "Test"
    post_body['product_category'] = "Test Category"
    post_body['product_profile'] = "general"

    # Save in database
    test_order.trans_ID = post_body['tran_id']
    test_order.payment_status = "VALID"
    test_order.save()
    
    payment = Payment()
    payment.patient = patient
    payment.name = post_body['cus_name']
    payment.email = post_body['cus_email']
    payment.phone = post_body['cus_phone']
    payment.address = post_body['cus_add1']
    payment.city = post_body['cus_city']
    payment.country = post_body['cus_country']
    payment.transaction_id = post_body['tran_id']
    payment.prescription = prescription
    
    payment.invoice_number = invoice_number
    
    payment_type = "test"
    payment.payment_type = payment_type
    payment.status = "Done"
    payment.currency_amount = post_body['total_amount']
    payment.save()
    
    # # Mailtrap
    patient_email = payment.patient.email
    patient_name = payment.patient.name
    patient_username = payment.patient.username
    patient_phone_number = payment.patient.phone_number
    
    ob = testCart.objects.filter(testorder__trans_ID=post_body['tran_id'])
    len_ob = len(ob)
        
    order_cart = []   
    for i in range(len_ob):
        order_cart.append(ob[i])
        
    for i in order_cart:
        test_id = i.item.test_info_id
        pres_test = Prescription_test.objects.filter(prescription=prescription).filter(test_info_id=test_id)
        #pres_test.test_info_pay_status = "Paid"
        pres_test.update(test_info_id=test_id,test_info_pay_status = "Paid")
    

    subject = "Payment Receipt for test"
    
    values = {
            "email":patient_email,
            "name":patient_name,
            "username":patient_username,
            "phone_number":patient_phone_number,
            "tran_id":post_body['tran_id'],
            "currency_amount":post_body['total_amount'],
            "order_cart":order_cart,
        }
    
    html_message = render_to_string('test_mail_payment_template.html', {'values': values})
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(subject, plain_message, 'hospital_admin@gmail.com',  [patient_email], html_message=html_message, fail_silently=False)
    except BadHeaderError:
        return HttpResponse('Invalid header found')
    
    # Reset cart
    testCart.objects.all().delete()
    
    final_amount = (int(float(post_body['total_amount'])))*100
    YOUR_DOMAIN = 'http://127.0.0.1:8000/sslcommerz/ssl-payment-request/'
    checkout_session = stripe.checkout.Session.create(
        line_items=[
            {
                # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                # TODO - replace hardcoded value of product price id to dynamic 
                'price_data':{
                    'currency': 'inr',
                    'unit_amount': final_amount,
                    'product_data':{
                        'name': 'Test Payment',
                    },
                }, 
                'quantity': 1,
            },
        ],
        mode='payment',
        success_url=YOUR_DOMAIN + 'ssl-payment-success' + '/',
        cancel_url=YOUR_DOMAIN + 'ssl-payment-cancel' + '/',
    )
    
    return redirect(checkout_session.url, code=303)

@csrf_exempt
def ssl_payment_success(request):
    return redirect('patient-dashboard')

@csrf_exempt
def ssl_payment_fail(request):
    return render(request, 'fail.html')

# @login_required


@csrf_exempt
def ssl_payment_cancel(request):
    return render(request, 'cancel.html')

@csrf_exempt
def payment_testing(request, pk):
    # order = Order.objects.get(id=pk)
    # ob = Cart.objects.filter(order__id=pk)
    
    tran_id = "SSLCZ_TEST_TGJOWR8G"
    # tran_id = "SSLCZ_TEST_74D530YZ"
    #ob = Cart.objects.filter(order__trans_ID=tran_id)
    ob = testCart.objects.filter(testorder__trans_ID=tran_id)
    

    len_ob = len(ob)
    
    list_id = []
    list_name = []
    for i in range(len_ob):
        list_id.append(ob[i].item.test_info_id)
        list_name.append(ob[i].item.test_name)
    
    order_cart = []   
    for i in range(len_ob):
        order_cart.append(ob[i])
    
    context = {'order': ob, 'len_ob': len_ob, 'list_id': list_id, 'list_name': list_name, 'order_cart': order_cart}

    return render(request, 'testing.html', context)
