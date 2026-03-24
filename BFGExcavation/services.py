import math


class ExcavationService:
    @staticmethod
    def calculate_supports(H, reference_el, h1_thickness, c_pc_thickness, d1_manual=0.5):
        c = c_pc_thickness
        h1 = h1_thickness

        L_base = round(h1 + c + 0.7, 4)
        H_upper = round(H - L_base, 4)

        is_error = False
        error_reasons = []
        warning = False
        warning_reasons = []

        if H < 3.1 or H > 10.1:
            warning = True
            warning_reasons.append(f"總開挖深度 H = {H:.2f}m，超出常規適用範圍 (3.1m ~ 10.1m)！")

        result_D = {}
        stages = 1

        if math.isclose(c, 0.1, abs_tol=0.001):
            L_eff = L_base
            if H_upper <= d1_manual:
                stages = 1
                result_D = {'D1': round(H_upper, 4), 'D2': round(L_eff, 4)}
            else:
                stages = 2
                D1 = d1_manual
                D2 = H_upper - D1
                if D2 > 3.2:
                    stages = 3
                    half = round((D2 / 2.0) * 10) / 10.0
                    if math.isclose(half * 2.0, D2, abs_tol=0.01):
                        new_D2 = half
                        new_D3 = half
                    else:
                        new_D2 = math.ceil((D2 / 2.0) * 10) / 10.0
                        new_D3 = round((D2 - new_D2) * 10) / 10.0
                        if new_D2 < new_D3:
                            new_D2, new_D3 = new_D3, new_D2
                    result_D = {'D1': D1, 'D2': round(new_D2, 4), 'D3': round(new_D3, 4), 'D4': round(L_eff, 4)}
                else:
                    result_D = {'D1': D1, 'D2': round(D2, 4), 'D3': round(L_eff, 4)}
        else:
            bottom_D = L_base / 2.0
            if H_upper <= d1_manual:
                stages = 2
                result_D = {'D1': round(H_upper, 4), 'D2': round(bottom_D, 4), 'D3': round(bottom_D, 4)}
            else:
                stages = 3
                D1 = d1_manual
                D2 = H_upper - D1
                result_D = {'D1': D1, 'D2': round(D2, 4), 'D3': round(bottom_D, 4), 'D4': round(bottom_D, 4)}

        keys = list(result_D.keys())
        for i, k in enumerate(keys):
            if i > 0 and i < len(keys) - 1:
                if result_D[k] > 3.2:
                    is_error = True
                    error_reasons.append(f"中間階支撐間距 {k} = {result_D[k]:.2f}m，超過建築規範安全上限 (3.2m)！")

        if not math.isclose(sum(result_D.values()), H, abs_tol=0.01):
            is_error = True
            error_reasons.append(f"所有分配的間距總和與實際開挖深度 H ({H:.2f}m) 兜不攏！")

        Z_coords = []
        current_z = reference_el
        for i, k in enumerate(keys):
            if i < len(keys) - 1:
                current_z -= result_D[k]
                Z_coords.append(round(current_z, 4))

        return {
            'D': result_D,
            'Z_coords': Z_coords,
            'is_error': is_error,
            'error_reasons': error_reasons,
            'warning': warning,
            'warning_reasons': warning_reasons,
            'stages': stages,
            'H': round(H, 4),
            'Reference_EL': round(reference_el, 4)
        }

    @staticmethod
    def process_foundation(foundation, d1_manual=None):
        elevations = [
            foundation.el_l1_start, foundation.el_l1_end,
            foundation.el_l2_start, foundation.el_l2_end,
            foundation.el_b1_start, foundation.el_b1_end,
            foundation.el_b2_start, foundation.el_b2_end
        ]

        max_el = max(elevations)
        min_el = min(elevations)

        if max_el - min_el <= 1.0:
            reference_el = sum(elevations) / 8.0
        else:
            reference_el = max_el

        reference_el = round(reference_el * 20) / 20.0

        final_el = foundation.column_base_el - foundation.h1_thickness - foundation.c_pc_thickness
        H = reference_el - final_el

        use_d1 = float(d1_manual) if d1_manual is not None else float(foundation.d1_manual)

        calc_result = ExcavationService.calculate_supports(
            H=H,
            reference_el=reference_el,
            h1_thickness=foundation.h1_thickness,
            c_pc_thickness=foundation.c_pc_thickness,
            d1_manual=use_d1
        )

        calc_result['bridge_id'] = foundation.bridge_id
        calc_result['project_code'] = foundation.project_code
        calc_result['geometry'] = {
            'B1': foundation.B1,
            'B2': foundation.B2,
            'L1': foundation.L1,
            'L2': foundation.L2,
        }
        calc_result['parameters'] = {
            'h1_thickness': foundation.h1_thickness,
            'c_pc_thickness': foundation.c_pc_thickness,
            'column_base_el': foundation.column_base_el,
            'd1_manual': foundation.d1_manual,
            'offset_dist': foundation.offset_dist,
            'skew_angle': getattr(foundation, 'skew_angle', 0.0),
            'el_l1_start': foundation.el_l1_start,
            'el_l1_end': foundation.el_l1_end,
            'el_l2_start': foundation.el_l2_start,
            'el_l2_end': foundation.el_l2_end,
            'el_b1_start': foundation.el_b1_start,
            'el_b1_end': foundation.el_b1_end,
            'el_b2_start': foundation.el_b2_start,
            'el_b2_end': foundation.el_b2_end,
            'B1': foundation.B1,
            'B2': foundation.B2,
            'L1': foundation.L1,
            'L2': foundation.L2,
        }
        calc_result['elevations'] = elevations
        calc_result['skew_angle'] = getattr(foundation, 'skew_angle', 0.0)
        calc_result['note'] = getattr(foundation, 'note', '')
        calc_result['excavation_plan'] = getattr(foundation, 'excavation_plan', '')
        calc_result['excavation_section'] = getattr(foundation, 'excavation_section', '')
        calc_result['bridge_name'] = getattr(foundation, 'bridge_name', '')
        calc_result['needs_review'] = getattr(foundation, 'needs_review', False)

        return calc_result
