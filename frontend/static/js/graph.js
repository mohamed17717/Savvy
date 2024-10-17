function activateNodeColor(node) {
  const currentColor = node.get("fill");
  const activeColor = "red";

  node.get("circle").set("fill", activeColor);
  node.isActive = true;

  return () => {
    node.get("circle").set("fill", currentColor);
    node.isActive = false;
  };
}

function reColorShardedIslandsNodes(nodes, series) {
  nodes.map((node) => {
    if (node.is_sharded_islands) {
      var circle = series.getDataItemById(node.id);
      circle.set("fill", "yellow");
      circle.get("circle").set("fill", "yellow");
    }
  });
}

async function toggleNodeChildren(
  dataItem,
  node,
  series,
  open,
  close,
  searchQuery
) {
  // toggle data in the tree (open / close)
  if (node.children_count === 0) {
    // do nothing
    node.isOpened = !node.isOpened;
  } else if (node.isOpened) {
    // close
    series.disableDataItem(dataItem);
    node.isOpened = false;
  } else if (node.children) {
    series.enableDataItem(dataItem);
    node.isOpened = true;
  } else {
    const newChildren = await graphChildren(node.id, searchQuery);
    if (newChildren.length > 1) {
      series.addChildData(dataItem, newChildren);
      node.isOpened = true;
      reColorShardedIslandsNodes(newChildren, series);
    }
  }

  node.isActive = node.isOpened;
  node.isActive ? open() : close();
}
let root;
async function startGraph(xData) {
  let data = {
    value: 0,
    children: await graphRoots(xData.searchQuery),
  };

  if (!!root) root.dispose();

  root = am5.Root.new("chartdiv");

  root.setThemes([am5themes_Animated.new(root)]);

  // var container = root.container.children.push(
  //   am5.Container.new(root, {
  //     width: am5.percent(100),
  //     height: am5.percent(100),
  //     layout: root.verticalLayout,
  //   })
  // );

  var zoomableContainer = root.container.children.push(
    am5.ZoomableContainer.new(root, {
      width: am5.p100,
      height: am5.p100,
      wheelable: true,
      pinchZoom: true,
    })
  );

  var zoomTools = zoomableContainer.children.push(
    am5.ZoomTools.new(root, {
      target: zoomableContainer,
    })
  );

  // var series = container.children.push(
  var series = zoomableContainer.contents.children.push(
    am5hierarchy.ForceDirected.new(root, {
      maskContent: false, //!important with zoomable containers

      singleBranchOnly: false,
      downDepth: 1,
      topDepth: 1,
      initialDepth: 1,
      valueField: "bookmarks_count",
      categoryField: "name",
      childDataField: "children",
      idField: "id",
      linkWithField: "linkWith",
      manyBodyStrength: -30,
      centerStrength: 0.8,

      minRadius: 20,
      maxRadius: am5.percent(50),
      manyBodyStrength: -10,
      nodePadding: 10,
    })
  );

  series.get("colors").setAll({ step: 2 });
  series.links.template.set("strength", 0.5);
  series.labels.template.set("minScale", 0.4);

  let disableNodeColor;

  let nodeClicked = false;
  series.nodes.template.events.on("click", async function (e) {
    if (nodeClicked) return;
    nodeClicked = true;
    const dataItem = e.target.dataItem;
    const node = dataItem.dataContext;
    const open = () => {
      xData.updateAppliedFilter("node", node.id);
      xData.removeAppliedFilter("exclude_node");

      if (disableNodeColor) disableNodeColor();
      disableNodeColor = activateNodeColor(dataItem);
    };
    const close = () => {
      xData.removeAppliedFilter("node");
      xData.removeAppliedFilter("exclude_node");
      if (disableNodeColor) disableNodeColor();
    };

    await toggleNodeChildren(
      dataItem,
      node,
      series,
      open,
      close,
      xData.searchQuery
    );
    nodeClicked = false;
  });

  series.labels.template.setAll({
    fontSize: 14,
    fill: am5.color(0x550000),
    text: "{name} ({bookmarks_count})",
    oversizedBehavior: "truncate",
    textAlign: "center",
  });

  series.nodes.template.set("tooltipText", "{name} ({bookmarks_count})");
  // series.nodes.template.set("tooltipText", "bookmarks count: ({bookmarks_count})");

  series.data.setAll([data]);
  series.set("selectedDataItem", series.dataItems[0]);

  reColorShardedIslandsNodes(data.children, series);

  series.appear(1000, 100);
}
