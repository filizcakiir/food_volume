# -*- coding: utf-8 -*-
from flask import jsonify

def handle_400(error):
    return jsonify({'success': False, 'error': 'Bad request', 'code': 'BAD_REQUEST', 'details': str(error) if hasattr(error, 'description') else None}), 400

def handle_401(error):
    return jsonify({'success': False, 'error': 'Unauthorized', 'code': 'UNAUTHORIZED'}), 401

def handle_403(error):
    return jsonify({'success': False, 'error': 'Forbidden', 'code': 'FORBIDDEN'}), 403

def handle_404(error):
    return jsonify({'success': False, 'error': 'Not found', 'code': 'NOT_FOUND'}), 404

def handle_500(error):
    return jsonify({'success': False, 'error': 'Internal server error', 'code': 'INTERNAL_SERVER_ERROR', 'details': str(error) if hasattr(error, 'description') else None}), 500

def handle_validation_error(error):
    return jsonify({'success': False, 'error': 'Validation error', 'code': 'VALIDATION_ERROR', 'details': error.messages if hasattr(error, 'messages') else str(error)}), 400
