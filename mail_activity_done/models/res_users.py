# Copyright 2018-22 ForgeFlow <http://www.forgeflow.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo import api, fields, models, modules


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def systray_get_activities(self):
        # Here we totally override the method. Not very nice, but
        # we should perhaps ask Odoo to add a hook here.
        query = """SELECT m.id, count(*), act.res_model as model,
                        CASE
                            WHEN %(today)s::date -
                            act.date_deadline::date = 0 Then 'today'
                            WHEN %(today)s::date -
                            act.date_deadline::date > 0 Then 'overdue'
                            WHEN %(today)s::date -
                            act.date_deadline::date < 0 Then 'planned'
                        END AS states
                    FROM mail_activity AS act
                    JOIN ir_model AS m ON act.res_model_id = m.id
                    WHERE user_id = %(user_id)s
                    AND act.done = False
                    GROUP BY m.id, states, act.res_model;
                    """
        self.env.cr.execute(
            query, {"today": fields.Date.context_today(self), "user_id": self.env.uid}
        )
        activity_data = self.env.cr.dictfetchall()
        model_ids = [a["id"] for a in activity_data]
        model_names = {
            n.id: n.display_name for n in self.env["ir.model"].sudo().browse(model_ids)
        }

        user_activities = {}
        for activity in activity_data:
            if not user_activities.get(activity["model"]):
                module = self.env[activity["model"]]._original_module
                icon = module and modules.module.get_module_icon(module)
                user_activities[activity["model"]] = {
                    "id": activity["id"],
                    "name": model_names[activity["id"]],
                    "model": activity["model"],
                    "icon": icon,
                    "total_count": 0,
                    "today_count": 0,
                    "overdue_count": 0,
                    "planned_count": 0,
                    "type": "activity",
                }
            user_activities[activity["model"]][
                "%s_count" % activity["states"]
            ] += activity["count"]
            if activity["states"] in ("today", "overdue"):
                user_activities[activity["model"]]["total_count"] += activity["count"]

        return list(user_activities.values())
