from flask import url_for, Response, request, redirect, flash, abort
from werkzeug.exceptions import RequestEntityTooLarge, UnsupportedMediaType
from flask_login import current_user, login_required

def htmx_redirect(endpoint, code=200):
    response = Response()
    response.headers["HX-Redirect"] = endpoint
    response.status_code = code

    return response

def resolve_redirect(endpoint, message=None):
    redirect_method = htmx_redirect if 'hx-request' in request.headers else redirect
    if message:
        flash(message.get('text', 'A meesage should appear'), message.get('type' ,'success'))
    return redirect_method(endpoint, code=302)

def htmx_request(view_func): 
    def wrapper_func(*args, **kwargs): 
        if 'hx-request' in request.headers: 
            return view_func(*args, **kwargs) 
        else: 
            return redirect(url_for('index')) 

    # renames wrapper for unique name to avoid: AssertionError: View function mapping is overwriting an existing endpoint function: wrapper_func
    wrapper_func.__name__ = view_func.__name__
    return wrapper_func

def roles_required(roles: list = []):
    def wrapper(view):
        @login_required
        def role_check(*args, **kwargs):
            if current_user.role not in roles:
                return resolve_redirect('403')
            return view(*args, **kwargs)
        role_check.__name__ = view.__name__
        return role_check
    return wrapper
        

        