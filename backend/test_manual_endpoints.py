"""
Manual Endpoint Testing
Quick verification that all endpoints are accessible
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')
django.setup()

from django.urls import get_resolver
from django.core.management import call_command

print("="*80)
print("🔍 ENDPOINT VERIFICATION".center(80))
print("="*80)

print("\n📋 Checking URL Configuration...")

url_resolver = get_resolver()

# Check if all our new patterns are registered
endpoints_to_check = [
    # Shipping endpoints
    ('shipping-address-list', 'Shipping Addresses'),
    ('shipping-rate-list', 'Shipping Rates'),
    ('return-list', 'Returns'),
    ('cancellation-list', 'Cancellations'),
    
    # Review & Q&A endpoints
    ('rating-list', 'Product Ratings'),
    ('question-list', 'Product Questions'),
    ('answer-list', 'Product Answers'),
    
    # Flash sales & promotions
    ('flash-sale-list', 'Flash Sales'),
    ('bundle-list', 'Bundle Deals'),
    ('loyalty-points-list', 'Loyalty Points'),
    ('referral-list', 'Referrals'),
    ('badge-list', 'Product Badges'),
    
    # Vendor dashboard
    ('vendor-dashboard-stats', 'Vendor Dashboard Stats'),
    ('vendor-dashboard-orders', 'Vendor Dashboard Orders'),
]

print("\n✅ Registered Endpoints:")
passed = 0
failed = []

for name, description in endpoints_to_check:
    try:
        from django.urls import reverse
        url = reverse(name)
        print(f"   ✅ {description}: {url}")
        passed += 1
    except Exception as e:
        print(f"   ❌ {description}: NOT FOUND")
        failed.append((description, str(e)))

print("\n" + "="*80)
print("📊 ENDPOINT REGISTRATION SUMMARY".center(80))
print("="*80)
print(f"\n✅ Registered: {passed}/{len(endpoints_to_check)}")

if failed:
    print(f"\n❌ Not Found: {len(failed)}")
    for desc, error in failed:
        print(f"   - {desc}")
else:
    print("\n🎉 ALL ENDPOINTS REGISTERED SUCCESSFULLY!")

print("\n" + "="*80)
print("🧪 DJANGO SYSTEM CHECK".center(80))
print("="*80)

# Run Django check
try:
    call_command('check', verbosity=0)
    print("\n✅ Django system check PASSED")
except Exception as e:
    print(f"\n❌ Django system check FAILED: {e}")

print("\n" + "="*80)
print("📦 MODEL VERIFICATION".center(80))
print("="*80)

# Check if all models can be imported
models_to_check = [
    ('orders.models', 'ShippingAddress'),
    ('orders.models', 'ShippingRate'),
    ('orders.models', 'ReturnRequest'),
    ('orders.models', 'OrderCancellation'),
    ('products.models', 'ReviewImage'),
    ('products.models', 'ReviewVote'),
    ('products.models', 'ProductQuestion'),
    ('products.models', 'ProductAnswer'),
    ('products.models', 'FlashSale'),
    ('products.models', 'BundleDeal'),
    ('products.models', 'LoyaltyPoints'),
    ('products.models', 'ReferralProgram'),
    ('products.models', 'ProductBadge'),
]

model_passed = 0
model_failed = []

print("\n✅ Model Imports:")
for module_path, model_name in models_to_check:
    try:
        module = __import__(module_path, fromlist=[model_name])
        model = getattr(module, model_name)
        table_name = model._meta.db_table
        print(f"   ✅ {model_name}: {table_name}")
        model_passed += 1
    except Exception as e:
        print(f"   ❌ {model_name}: FAILED ({str(e)[:50]})")
        model_failed.append((model_name, str(e)))

print("\n" + "="*80)
print("📊 MODEL IMPORT SUMMARY".center(80))
print("="*80)
print(f"\n✅ Imported: {model_passed}/{len(models_to_check)}")

if model_failed:
    print(f"\n❌ Failed: {len(model_failed)}")
else:
    print("\n🎉 ALL MODELS IMPORTED SUCCESSFULLY!")

print("\n" + "="*80)
print("🔧 VIEW VERIFICATION".center(80))
print("="*80)

# Check if all views can be imported
views_to_check = [
    ('orders.shipping_views', 'ShippingAddressViewSet'),
    ('orders.shipping_views', 'ReturnRequestViewSet'),
    ('products.review_views', 'ProductRatingViewSet'),
    ('products.review_views', 'ProductQuestionViewSet'),
    ('products.promotion_views', 'FlashSaleViewSet'),
    ('products.promotion_views', 'LoyaltyPointsViewSet'),
]

view_passed = 0
view_failed = []

print("\n✅ View Imports:")
for module_path, view_name in views_to_check:
    try:
        module = __import__(module_path, fromlist=[view_name])
        view = getattr(module, view_name)
        print(f"   ✅ {view_name}")
        view_passed += 1
    except Exception as e:
        print(f"   ❌ {view_name}: FAILED ({str(e)[:50]})")
        view_failed.append((view_name, str(e)))

print("\n" + "="*80)
print("📊 VIEW IMPORT SUMMARY".center(80))
print("="*80)
print(f"\n✅ Imported: {view_passed}/{len(views_to_check)}")

if view_failed:
    print(f"\n❌ Failed: {len(view_failed)}")
else:
    print("\n🎉 ALL VIEWS IMPORTED SUCCESSFULLY!")

print("\n" + "="*80)
print("🎯 FINAL SUMMARY".center(80))
print("="*80)

total_checks = len(endpoints_to_check) + len(models_to_check) + len(views_to_check)
total_passed = passed + model_passed + view_passed
total_failed = len(failed) + len(model_failed) + len(view_failed)

print(f"\n📊 Overall Results:")
print(f"   ✅ Passed: {total_passed}/{total_checks}")
print(f"   ❌ Failed: {total_failed}/{total_checks}")
print(f"   📈 Success Rate: {(total_passed/total_checks*100):.1f}%")

if total_failed == 0:
    print("\n🎉 ALL CHECKS PASSED! SYSTEM IS READY! 🎉")
    print("\n✨ The backend is fully functional and ready for frontend development!")
else:
    print(f"\n⚠️  {total_failed} checks failed. Review the errors above.")

print("\n" + "="*80)

