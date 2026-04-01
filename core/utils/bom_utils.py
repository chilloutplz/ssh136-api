# product/services/bom_utils.py
from collections import defaultdict
from product.models import BOM

def check_bom_cycle(parent, component):
    """
    parent → component 관계를 추가했을 때 순환이 생기는지 검사.
    DFS를 메모리 기반으로 수행하여 N+1 쿼리 문제를 방지.
    """
    # 모든 BOM 관계를 한 번에 가져옴
    all_boms = BOM.objects.values_list("parent_id", "component_id")

    # 그래프 형태로 변환: parent_id → [component_ids...]
    graph = {}
    for p_id, c_id in all_boms:
        graph.setdefault(p_id, []).append(c_id)

    # DFS 탐색
    def dfs(node_id, target_id, visited):
        if node_id == target_id:
            return True
        if node_id not in graph:
            return False
        for child_id in graph[node_id]:
            if child_id in visited:
                continue
            visited.add(child_id)
            if dfs(child_id, target_id, visited):
                return True
        return False

    return dfs(component.id, parent.id, set())


def explode_bom(product, quantity=1):
    """
    전개 BOM (Explosion BOM)
    특정 product를 기준으로 모든 하위 부품과 총 소요량을 계산한다.
    """
    result = defaultdict(float)

    def dfs(current_product, multiplier):
        # 현재 product의 BOM 가져오기
        boms = BOM.objects.filter(parent=current_product, is_active=True).select_related("component")
        for bom in boms:
            required_qty = multiplier * float(bom.quantity)
            result[bom.component_id] += required_qty
            # component가 또 다른 BOM의 parent일 수 있으므로 재귀 호출
            dfs(bom.component, required_qty)

    dfs(product, quantity)
    return result
