import json
from datetime import datetime
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone


def generate_order_receipt(order):
    """
    Generate a JSON receipt for an order
    
    Args:
        order: Order object
    
    Returns:
        Dictionary with receipt data
    """
    # Get order items
    items = []
    for vendor_order in order.vendor_orders.all():
        for item in vendor_order.items.all():
            items.append({
                'product_name': item.product.name if item.product else 'Unknown Product',
                'sku_code': item.sku.sku_code if item.sku else 'N/A',
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'total': float(item.quantity * item.unit_price),
                'vendor': vendor_order.vendor.store_name
            })
    
    # Create receipt data
    # Handle both guest and registered user orders
    if order.is_guest:
        customer_info = {
            'name': order.guest_name or 'Guest Customer',
            'email': order.guest_email
        }
    else:
        customer_info = {
            'name': f"{order.user.first_name} {order.user.last_name}" if order.user else 'Unknown',
            'email': order.user.email if order.user else 'N/A'
        }
    
    receipt_data = {
        'receipt_id': str(order.id),
        'date': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'customer': customer_info,
        'payment_method': order.get_payment_method_display(),
        'shipping_address': order.shipping_address,
        'items': items,
        'subtotal': float(order.subtotal_amount),
        'discount': float(order.discount_amount),
        'total': float(order.total_amount),
        'currency': order.currency.upper(),
        'status': order.get_status_display()
    }
    
    return receipt_data


def order_receipt_json(order):
    """
    Generate a JSON receipt for an order
    
    Args:
        order: Order object
    
    Returns:
        HttpResponse with JSON receipt
    """
    receipt_data = generate_order_receipt(order)
    return HttpResponse(
        json.dumps(receipt_data, indent=4),
        content_type='application/json'
    )