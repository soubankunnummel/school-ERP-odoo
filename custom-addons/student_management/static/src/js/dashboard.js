// /** @odoo-module **/
// /**
//  * dashboard.js — School Dashboard JS widget
//  * ==========================================
//  * MERN equivalent: a React component that fetches stats and renders charts.
//  *
//  * Odoo 16/17 uses OWL (Odoo Web Library) — a React-like component framework.
//  * owl.Component  ≈  React.Component
//  * owl.useState   ≈  React.useState
//  * owl.onMounted  ≈  useEffect(() => {}, [])
//  *
//  * This registers a simple notification that runs when the school module loads.
//  */

// import { registry } from "@web/core/registry";
// import { Component, useState, onMounted } from "@odoo/owl";

// /**
//  * SchoolDashboardNotice — a tiny OWL component
//  * Equivalent to a React functional component with hooks.
//  */
// class SchoolDashboardNotice extends Component {
//     static template = "student_management.DashboardNotice";

//     setup() {
//         // owl.useState ≈ React.useState
//         this.state = useState({
//             loaded: false,
//             school_name: "Smart School ERP",
//         });

//         // owl.onMounted ≈ React.useEffect(() => {}, [])
//         onMounted(async () => {
//             try {
//                 // RPC call to Odoo ORM — MERN: axios.get('/api/settings')
//                 const result = await this.env.services.orm.searchRead(
//                     "school.settings",
//                     [],
//                     ["school_name", "academic_year"],
//                     { limit: 1 }
//                 );
//                 if (result && result.length > 0) {
//                     this.state.school_name = result[0].school_name || "Smart School ERP";
//                 }
//             } catch (e) {
//                 console.warn("School ERP: Could not load settings.", e);
//             } finally {
//                 this.state.loaded = true;
//             }
//         });
//     }
// }

// // Register as a systray item (top-right nav area)
// // MERN equivalent: adding a component to your navbar layout
// registry.category("systray").add("school_dashboard_notice", {
//     Component: SchoolDashboardNotice,
//     sequence: 1,
// });

console.log(
    "%c🏫 Smart School ERP loaded",
    "color: #2c3e50; font-weight: bold; font-size: 14px;"
);
