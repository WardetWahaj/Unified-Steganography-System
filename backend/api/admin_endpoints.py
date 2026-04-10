"""
Admin endpoints for user management
"""
import os
import sys
from datetime import datetime, timedelta
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import JSONResponse
from models import Database, UserManager

admin_router = APIRouter(prefix="/api/admin", tags=["admin"])
db = Database()
user_manager = UserManager(db=db)

def get_current_user(request: Request):
    """Extract user from session cookie or header"""
    session_token = request.cookies.get('session_id') or request.headers.get('X-Session-Token')
    print(f'[DEBUG] get_current_user: session_token={session_token}')
    
    if not session_token:
        print(f'[DEBUG] No session token found. Cookies: {request.cookies}')
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_id = db.get_session_user(session_token)
    print(f'[DEBUG] get_current_user: user_id from session={user_id}')
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return dict(user)


def verify_admin(request: Request):
    """Verify that the current user is an admin"""
    user = get_current_user(request)
    # For now, we'll allow all authenticated users (can add role check later)
    return user


# ═══════════════════════════════════════════════════════════
# GET ALL USERS
# ═══════════════════════════════════════════════════════════

@admin_router.get("/users")
async def get_users(request: Request, limit: int = 50, offset: int = 0, search: str = ""):
    """
    Get all users with pagination and search
    """
    try:
        verify_admin(request)
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Build search query - include status column
        query = "SELECT id, username, email, fullname, status, created_at FROM users"
        params = []
        
        if search:
            query += " WHERE username LIKE ? OR email LIKE ?"
            search_term = f"%{search}%"
            params = [search_term, search_term]
        
        # Get total count
        count_query = "SELECT COUNT(*) FROM users"
        if search:
            count_query += " WHERE username LIKE ? OR email LIKE ?"
        
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # Get paginated results
        query += f" LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        users = cursor.fetchall()
        conn.close()
        
        return {
            'success': True,
            'data': [
                {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2] if user[2] else 'N/A',
                    'fullname': user[3] if user[3] else 'N/A',
                    'status': user[4] if user[4] else 'active',
                    'created_at': user[5],
                    'role': 'admin' if user[1] == 'admin' else 'user'
                }
                for user in users
            ],
            'total': total,
            'limit': limit,
            'offset': offset
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# CREATE NEW USER
# ═══════════════════════════════════════════════════════════

@admin_router.post("/users")
async def create_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(""),
    fullname: str = Form("")
):
    """
    Create a new user
    """
    try:
        verify_admin(request)
        
        # Validate inputs
        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters")
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters")
        
        # Check if user exists
        if db.user_exists(username):
            raise ValueError("Username already exists")
        
        # Create user
        result = user_manager.signup(username, password)
        user_id = result['user_id']
        
        # Update email and fullname
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET email = ?, fullname = ?
            WHERE id = ?
        ''', (email, fullname, user_id))
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'message': 'User created successfully',
            'user_id': user_id,
            'username': username
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# UPDATE USER
# ═══════════════════════════════════════════════════════════

@admin_router.put("/users/{user_id}")
async def update_user(request: Request, user_id: int, email: Optional[str] = Form(None), fullname: Optional[str] = Form(None), status: Optional[str] = Form(None)):
    """
    Update user information (email, fullname, status)
    Status can be: active, suspended
    """
    try:
        print(f'[DEBUG] PUT /users/{user_id} called')
        print(f'[DEBUG] Form data: email={email}, fullname={fullname}, status={status}')
        
        verify_admin(request)
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id, username FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            raise ValueError("User not found")
        
        username = user[1]
        print(f'[DEBUG] Updating user: {username}')
        
        # SECURITY: Prevent suspending the admin user
        if status == 'suspended' and username == 'admin':
            conn.close()
            raise ValueError("Cannot suspend the admin user")
        
        # Update fields if provided
        if email or fullname or status:
            updates = []
            values = []
            if email:
                updates.append("email = ?")
                values.append(email)
            if fullname:
                updates.append("fullname = ?")
                values.append(fullname)
            if status:
                print(f'[DEBUG] Status update requested: {status}')
                if status not in ['active', 'suspended']:
                    conn.close()
                    raise ValueError("Invalid status. Must be 'active' or 'suspended'")
                updates.append("status = ?")
                values.append(status)
            
            if updates:
                values.append(user_id)
                update_query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
                print(f'[DEBUG] Executing: {update_query} with values: {values}')
                cursor.execute(update_query, values)
        
        # IF SUSPENDING, INVALIDATE ALL EXISTING SESSIONS
        if status == 'suspended':
            print(f'[DEBUG] Invalidating all sessions for user {user_id}')
            cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        
        conn.commit()
        conn.close()
        print(f'[DEBUG] User {user_id} updated successfully')
        
        return {
            'success': True,
            'message': f'User updated successfully'
        }
    
    except ValueError as e:
        print(f'[ERROR] ValueError: {e}')
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f'[ERROR] Exception: {type(e).__name__}: {e}')
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# DELETE USER
# ═══════════════════════════════════════════════════════════

@admin_router.delete("/users/{user_id}")
async def delete_user(request: Request, user_id: int):
    """
    Delete a user with security checks
    """
    try:
        current_user = verify_admin(request)
        current_user_id = current_user.get('id')
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            raise ValueError("User not found")
        
        username = user[0]
        
        # SECURITY: Prevent deleting yourself
        if current_user_id == user_id:
            conn.close()
            raise ValueError("Cannot delete your own account")
        
        # SECURITY: Prevent deleting admin user
        if username == 'admin':
            conn.close()
            raise ValueError("Cannot delete the admin user")
        
        # SECURITY: Check if this would remove the last admin
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        admin_count = cursor.fetchone()[0]
        if admin_count == 1 and username == 'admin':
            conn.close()
            raise ValueError("Cannot delete the last admin user")
        
        # Delete user
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        # Delete sessions
        cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'message': f'User {username} deleted successfully'
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# GET ADMIN STATS
# ═══════════════════════════════════════════════════════════

@admin_router.get("/stats")
async def get_stats(request: Request):
    """
    Get admin dashboard statistics - NOW WITH REAL-TIME DATA
    """
    try:
        verify_admin(request)
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get user count
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        # Get active sessions count
        cursor.execute("SELECT COUNT(*) FROM sessions WHERE expires_at > datetime('now')")
        active_sessions = cursor.fetchone()[0]
        
        # Get operation counts from audit logs
        cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE action LIKE '%HIDE%' AND status = 'success'")
        hide_operations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE action LIKE '%EXTRACT%' AND status = 'success'")
        extract_operations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE status = 'failure'")
        failed_operations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE action LIKE '%RSA%'")
        rsa_operations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE action LIKE '%PASSWORD%'")
        password_operations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE action LIKE '%HYBRID%'")
        hybrid_operations = cursor.fetchone()[0]
        
        total_operations = hide_operations + extract_operations
        
        conn.close()
        
        return {
            'success': True,
            'total_users': user_count,
            'active_sessions': active_sessions,
            'total_operations': total_operations,
            'storage_used': 0,  # Would need to calculate from file system
            'hide_operations': hide_operations,
            'extract_operations': extract_operations,
            'failed_operations': failed_operations,
            'rsa_operations': rsa_operations,
            'password_operations': password_operations,
            'hybrid_operations': hybrid_operations,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# GET AUDIT LOG
# ═══════════════════════════════════════════════════════════

@admin_router.get("/audit-log")
async def get_audit_log(request: Request, limit: int = 50):
    """
    Get audit log with REAL-TIME data from the database
    """
    try:
        verify_admin(request)
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get latest audit logs
        cursor.execute('''
            SELECT id, username, action, resource, status, details, ip_address, created_at 
            FROM audit_logs 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (limit,))
        
        logs = cursor.fetchall()
        conn.close()
        
        # Format logs for frontend
        formatted_logs = [
            {
                'id': log[0],
                'user': log[1] or 'system',
                'action': log[2] or 'UNKNOWN',
                'resource': log[3] or 'N/A',
                'status': log[4] or 'pending',
                'details': log[5] or 'No details',
                'ipAddress': log[6] or 'N/A',
                'timestamp': log[7],
            }
            for log in logs
        ]
        
        return {
            'success': True,
            'data': formatted_logs,
            'total': len(formatted_logs),
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
