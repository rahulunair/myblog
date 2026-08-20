-- Keep Markdown tables structurally intact while giving wide evidence tables
-- one keyboard-scrollable container on narrow screens.
function Table(table)
  local attributes = {
    role = "region",
    ["aria-label"] = "Scrollable data table",
    tabindex = "0"
  }
  return pandoc.Div({ table }, pandoc.Attr("", { "table-scroll" }, attributes))
end
