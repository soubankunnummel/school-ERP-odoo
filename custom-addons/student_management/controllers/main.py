# -*- coding: utf-8 -*-
"""
controllers/main.py — JSON API Controllers
============================================
MERN equivalent: Express.js router / route handlers
These are HTTP endpoints you can call from external systems or your own JS.

Example:
  GET  /school/api/students          → list all students
  GET  /school/api/students/<id>     → get one student
  POST /school/api/sync-avatar/<id>  → re-fetch avatar from dummyjson API
  GET  /school/api/dashboard         → dashboard stats JSON
"""
import json
from odoo import http
from odoo.http import request


class SchoolApiController(http.Controller):

    # ------------------------------------------------------------------ #
    #  Students API                                                        #
    # ------------------------------------------------------------------ #
    @http.route('/school/api/students', type='json', auth='user', methods=['POST'])
    def get_students(self, **kwargs):
        """
        Returns all active students as JSON.
        MERN: GET /api/students → res.json(students)
        """
        students = request.env['school.student'].sudo().search([
            ('active', '=', True)
        ])
        return {
            'status': 'ok',
            'count': len(students),
            'data': [
                {
                    'id': s.id,
                    'name': s.name,
                    'roll_number': s.roll_number,
                    'class': s.class_id.name if s.class_id else None,
                    'attendance_percentage': s.attendance_percentage,
                    'state': s.state,
                    'avatar_url': s.avatar_url,
                }
                for s in students
            ]
        }

    @http.route('/school/api/students/<int:student_id>', type='json',
                auth='user', methods=['POST'])
    def get_student(self, student_id, **kwargs):
        """
        Returns a single student's details.
        MERN: GET /api/students/:id
        """
        student = request.env['school.student'].sudo().browse(student_id)
        if not student.exists():
            return {'status': 'error', 'message': 'Student not found'}

        return {
            'status': 'ok',
            'data': {
                'id': student.id,
                'name': student.name,
                'roll_number': student.roll_number,
                'age': student.age,
                'email': student.email,
                'class': student.class_id.name if student.class_id else None,
                'subjects': [s.name for s in student.subject_ids],
                'attendance': {
                    'total': student.total_attendance,
                    'present': student.present_days,
                    'absent': student.absent_days,
                    'percentage': student.attendance_percentage,
                },
                'state': student.state,
                'avatar_url': student.avatar_url,
                'has_fee_discount': student.has_fee_discount,
                'total_fee_due': student.total_fee_due,
            }
        }

    @http.route('/school/api/sync-avatar/<int:student_id>', type='json',
                auth='user', methods=['POST'])
    def sync_avatar(self, student_id, **kwargs):
        """
        Triggers a fresh avatar fetch from dummyjson.com API.
        MERN: POST /api/students/:id/sync-avatar
        """
        student = request.env['school.student'].sudo().browse(student_id)
        if not student.exists():
            return {'status': 'error', 'message': 'Student not found'}
        student._fetch_avatar_from_api()
        return {
            'status': 'ok',
            'message': f"Avatar synced for {student.name}",
            'avatar_url': student.avatar_url,
        }

    # ------------------------------------------------------------------ #
    #  Dashboard Stats API                                                 #
    # ------------------------------------------------------------------ #
    @http.route('/school/api/dashboard', type='json', auth='user', methods=['POST'])
    def dashboard_stats(self, **kwargs):
        """
        Returns aggregated dashboard stats.
        MERN: GET /api/dashboard → aggregation pipeline result
        """
        env = request.env
        Student = env['school.student'].sudo()
        Teacher = env['school.teacher'].sudo()
        Class = env['school.class'].sudo()
        Attendance = env['school.attendance'].sudo()

        total_students = Student.search_count([('active', '=', True)])
        confirmed_students = Student.search_count([('state', '=', 'confirmed')])
        graduated_students = Student.search_count([('state', '=', 'graduated')])
        total_teachers = Teacher.search_count([('active', '=', True)])
        total_classes = Class.search_count([('active', '=', True)])

        # Attendance today
        today = http.request.env['school.attendance'].sudo().search([
            ('date', '=', str(http.request.env.cr.now().date()))
        ])
        present_today = len(today.filtered(lambda r: r.status == 'present'))
        total_today = len(today)

        return {
            'status': 'ok',
            'data': {
                'total_students': total_students,
                'confirmed_students': confirmed_students,
                'graduated_students': graduated_students,
                'total_teachers': total_teachers,
                'total_classes': total_classes,
                'attendance_today': {
                    'present': present_today,
                    'total': total_today,
                    'percentage': round(present_today / total_today * 100, 2)
                    if total_today else 0,
                }
            }
        }
