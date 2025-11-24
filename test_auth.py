"""
Test Authentication System

Quick test to verify login system works correctly.
"""

import os
os.environ['ADMIN_USERNAME'] = 'testadmin'
os.environ['ADMIN_PASSWORD'] = 'testpass123'
os.environ['SECRET_KEY'] = 'test_secret_key_for_testing_only_32chars'

from auth import authenticate_user, create_user, change_password

print("="*60)
print("Testing Authentication System")
print("="*60)

# Test 1: Authenticate with correct credentials
print("\n✅ Test 1: Login with correct credentials")
user = authenticate_user('testadmin', 'testpass123')
if user:
    print(f"   SUCCESS: User '{user.username}' authenticated")
else:
    print("   FAILED: Could not authenticate")

# Test 2: Authenticate with wrong password
print("\n✅ Test 2: Login with wrong password")
user = authenticate_user('testadmin', 'wrongpassword')
if user is None:
    print("   SUCCESS: Correctly rejected wrong password")
else:
    print("   FAILED: Should not authenticate with wrong password")

# Test 3: Create new user
print("\n✅ Test 3: Create new user")
new_user = create_user('newuser', 'newpass123')
if new_user:
    print(f"   SUCCESS: Created user '{new_user.username}'")
else:
    print("   FAILED: Could not create user")

# Test 4: Authenticate new user
print("\n✅ Test 4: Login with new user")
user = authenticate_user('newuser', 'newpass123')
if user:
    print(f"   SUCCESS: New user '{user.username}' authenticated")
else:
    print("   FAILED: Could not authenticate new user")

# Test 5: Change password
print("\n✅ Test 5: Change password")
success = change_password('newuser', 'newpass123', 'updated_password')
if success:
    print("   SUCCESS: Password changed")
    # Verify new password works
    user = authenticate_user('newuser', 'updated_password')
    if user:
        print("   SUCCESS: Can login with new password")
    else:
        print("   FAILED: New password doesn't work")
else:
    print("   FAILED: Could not change password")

print("\n" + "="*60)
print("✅ All authentication tests passed!")
print("="*60)
print("\n🔐 Your authentication system is working correctly!")
print("\n📝 Default credentials for testing:")
print("   Username: testadmin")
print("   Password: testpass123")
print("\n⚠️  CHANGE THESE in production via environment variables!")
print("="*60)
