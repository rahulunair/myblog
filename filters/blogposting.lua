local SITE_URL = "https://blog.rahul.onl"

-- Keep authoring notes in the source without shipping them in page HTML.
function RawBlock(block)
  if block.format == "html" and block.text:match("^%s*<!%-%-") then
    return {}
  end
end

local function text(meta, key)
  local value = meta[key]
  if value == nil then
    return nil
  end
  local rendered = pandoc.utils.stringify(value)
  if rendered == "" then
    return nil
  end
  return rendered
end

local function input_path()
  local path = quarto.doc.input_file or ""
  path = path:gsub("\\\\", "/")
  if quarto.project.directory then
    path = pandoc.path.make_relative(path, quarto.project.directory)
  end
  return path:gsub("^%./", "")
end

local function output_url(path)
  path = path:gsub("%.qmd$", ".html"):gsub("%.md$", ".html")
  return SITE_URL .. "/" .. path
end

local function absolute_image(path, input)
  if path == nil or path == "" then
    return nil
  end
  if path:match("^https?://") then
    return path
  end
  path = path:gsub("^/", "")
  local directory = input:match("^(.*)/[^/]+$")
  if directory and not path:match("^posts/") and not path:match("^assets/") then
    path = directory .. "/" .. path
  end
  return SITE_URL .. "/" .. path
end

local function category_list(meta)
  local result = {}
  local categories = meta.categories
  if categories == nil then
    return result
  end
  for _, category in ipairs(categories) do
    table.insert(result, pandoc.utils.stringify(category))
  end
  return result
end

function Meta(meta)
  if not quarto.doc.is_format("html") then
    return meta
  end

  local input = input_path()
  local url = output_url(input)
  if input == "index.md" or input == "index.qmd" then
    url = SITE_URL .. "/"
  end

  local head = {
    '<meta property="og:url" content="' .. url .. '">',
    '<meta property="og:type" content="' ..
      (input:match("^posts/") and "article" or "website") .. '">'
  }

  if input:match("^posts/") then
    local published = text(meta, "date-published") or
      input:match("^posts/(%d%d%d%d%-%d%d%-%d%d)-") or text(meta, "date")
    local schema = {
      ["@context"] = "https://schema.org",
      ["@type"] = "BlogPosting",
      ["@id"] = url .. "#article",
      headline = text(meta, "title"),
      description = text(meta, "description"),
      datePublished = published,
      mainEntityOfPage = { ["@type"] = "WebPage", ["@id"] = url },
      author = { ["@id"] = SITE_URL .. "/#author" },
      publisher = { ["@id"] = SITE_URL .. "/#author" },
      isPartOf = { ["@id"] = SITE_URL .. "/#blog" },
      image = absolute_image(text(meta, "image"), input) or
        SITE_URL .. "/assets/site-card.png",
      keywords = category_list(meta)
    }

    local modified = text(meta, "date-modified")
    if modified then
      schema.dateModified = modified
    end

    table.insert(
      head,
      '<script type="application/ld+json">' .. pandoc.json.encode(schema) .. "</script>"
    )
  elseif input == "about.qmd" then
    local profile = {
      ["@context"] = "https://schema.org",
      ["@type"] = "ProfilePage",
      ["@id"] = SITE_URL .. "/about.html#profile",
      url = SITE_URL .. "/about.html",
      name = "About Rahul Nair",
      mainEntity = { ["@id"] = SITE_URL .. "/#author" }
    }
    table.insert(
      head,
      '<script type="application/ld+json">' .. pandoc.json.encode(profile) .. "</script>"
    )
  end

  local block = pandoc.MetaBlocks({
    pandoc.RawBlock("html", table.concat(head, "\n"))
  })
  local includes = meta["header-includes"] or pandoc.MetaList({})
  table.insert(includes, block)
  meta["header-includes"] = includes
  return meta
end
