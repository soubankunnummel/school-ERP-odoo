# -*- coding: utf-8 -*-
{
    'name': 'Smart School ERP',
    'version': '1.0.0',
    'category': 'Education',
    'summary': 'Advanced Student Management System with full ERP features',
    'description': """
        Smart School ERP - Complete Student Management System
        =====================================================
        Features:
        - Student, Teacher, Class, Subject Management
        - Attendance Tracking with auto-computed stats
        - Fee Management with smart discounts
        - Workflow (Draft → Confirmed → Graduated)
        - Role-based Security (Admin / Teacher / Student)
        - QWeb PDF Reports
        - External API Integration (DummyJSON for avatars)
        - Dashboard with stats
        - Settings & Automation (Cron)
    """,
    'author': 'School ERP Dev',
    'depends': ['base', 'mail', 'web'],
    'data': [
        # Security
        'security/school_security.xml',
        'security/ir.model.access.csv',

        # Data
        'data/school_data.xml',
        'data/school_cron.xml',

        # Views
        'views/student_views.xml',
        'views/teacher_views.xml',
        'views/class_views.xml',
        'views/subject_views.xml',
        'views/attendance_views.xml',
        'views/fee_views.xml',
        'views/dashboard_views.xml',
        'views/settings_views.xml',

        # Reports
        'reports/student_report.xml',
        'reports/attendance_report.xml',

        # Menu
        'views/school_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'student_management/static/src/css/school.css',
            'student_management/static/src/js/dashboard.js',
        ],
    },
    'installable': True,
    'application': True,
    'sequence': 100,
    'license': 'LGPL-3',
}
