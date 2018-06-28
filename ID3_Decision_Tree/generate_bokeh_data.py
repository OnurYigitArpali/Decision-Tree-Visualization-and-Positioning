from ID3_Decision_Tree.id3_2 import generate_tree


def get_depth(node, visited = {}):
    if not node.children:
        node.depth = 1
        visited[node] = False
        return 1

    max_depth = max([get_depth(child, visited) for child in node.children])

    node.depth = max_depth + 1
    visited[node] = False
    return max_depth + 1


def get_width(node, level):
    if node is None:
        return 0
    if level == 1:
        return 1
    elif level > 1:
        return sum([get_width(child, level-1) for child in node.children])


def get_max_width(node):
    max_width = 0
    h = get_depth(node)
    level_widths = []
    for i in range(1, h+1):
        width = get_width(node, i)
        level_widths.append(width)
        if width > max_width:
            max_width = width
    return max_width, level_widths



def generate_bokeh_data(source, root, depth, visited):
    width_index = [1] * depth

    queue = []
    queue.append(root)

    visited[root] = True

    while queue:

        popped_node = queue.pop(0)

        source["x"].append(popped_node.depth)
        source["y"].append(width_index[popped_node.depth-1])

        if popped_node.name == "":
            source["attribute_type"].append("classAttr")
        else:
            source["attribute_type"].append(popped_node.name)

        source["stat_value"].append(popped_node.value)
        width_index[popped_node.depth - 1] += 1

        for child in popped_node.children:
            if visited[child] == False:
                queue.append(child)
                visited[child] = True


def get_bokeh_data(method):
    root = generate_tree(method)
    visited = {}
    depth = get_depth(root, visited)
    width, level_width = get_max_width(root)
    source = { "x": [], "y": [], "attribute_type": [], "stat_value": []}
    generate_bokeh_data(source, root, depth, visited)

    return source, depth, width
