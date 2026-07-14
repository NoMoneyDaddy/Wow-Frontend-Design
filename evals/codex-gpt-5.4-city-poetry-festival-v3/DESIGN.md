---
version: alpha
name: 城市詩祭設計系統
description: 都市詩祭探索網站的編輯式視覺契約，服務手機與桌機讀者的活動探索。
colors:
  primary: "#1F2421"
  on-primary: "#F7F1E8"
  surface: "#F7F1E8"
  on-surface: "#1F2421"
  surface-strong: "#E4D8C6"
  accent: "#A33B2E"
  accent-soft: "#D9B39B"
  line: "#8A7B68"
typography:
  display:
    fontFamily: "Baskerville, Georgia, Times New Roman, serif"
    fontSize: 3rem
    fontWeight: "700"
    lineHeight: 1.05
    letterSpacing: -0.03em
  title:
    fontFamily: "Baskerville, Georgia, Times New Roman, serif"
    fontSize: 1.5rem
    fontWeight: "700"
    lineHeight: 1.15
  body:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, PingFang TC, Noto Sans TC, Microsoft JhengHei, sans-serif"
    fontSize: 1rem
    fontWeight: "400"
    lineHeight: 1.7
  meta:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, PingFang TC, Noto Sans TC, Microsoft JhengHei, sans-serif"
    fontSize: 0.875rem
    fontWeight: "600"
    lineHeight: 1.4
    letterSpacing: 0.02em
rounded:
  sm: 0.35rem
  md: 0.9rem
spacing:
  xs: 0.4rem
  sm: 0.75rem
  md: 1rem
  lg: 1.5rem
  xl: 2.5rem
components:
  page-shell:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.md}"
    padding: "{spacing.lg}"
  nav-link:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.meta}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.meta}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  status-open:
    backgroundColor: "{colors.surface-strong}"
    textColor: "{colors.on-surface}"
    typography: "{typography.meta}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
  status-wait:
    backgroundColor: "{colors.accent-soft}"
    textColor: "{colors.primary}"
    typography: "{typography.meta}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
  status-full:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.on-primary}"
    typography: "{typography.meta}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
---

# 城市詩祭設計系統

## Overview

這個網站給一般讀者快速找到詩人、場地、日期與活動線索。概念是「把城市節目摺頁攤開成可探索的詩刊版面」，讓讀者先被編輯判斷帶路，再進入各場活動細節。整體氣質是沉著、文學、可行走；拒絕科技儀表板感與通用行銷頁套路。

## Colors

底色 `surface` 是帶紙感的暖米色，承接紙本詩刊與摺頁語境。`primary` 只用於導覽骨架、主要按鈕與高對比標題，像鉛字油墨。`accent` 是節目標記色，只在狀態、索引重點與少量分隔標註出現，不拿來鋪滿大區塊。`line` 用於細分隔與欄位對齊，讓內容像被編輯標尺整理過。

## Typography

Display 與標題採 serif，負責詩意與節奏；內文與功能資訊採 CJK 友善 sans，負責可讀性與密度。日期、場地、狀態、導覽等功能字用 `meta`，維持單行與穩定節拍。`zh-Hant` 以自然中文語序與全形標點為主，長標題允許換行，但按鈕、日期、場地與狀態標籤維持單行呈現。

## Layout

桌機採三段式：導覽橫帶、主編輯區、活動索引。直排詩句欄與橫向活動內容並置，明確展示「詩行」與「節目表」的關係。手機改成單欄，但不是單純堆疊：直排區改為短橫幅引言，主題與行動入口提早露出，活動索引改成緊湊列表，保留每場的日期、場地、主題與狀態。

## Elevation & Depth

層次主要靠留白、底色切換、細線與局部色塊，不靠大量陰影。首頁只有少數懸浮感：主編輯摘要與重要狀態籤。這讓視覺更接近真實節目單與刊物排版，而不是卡片拼貼。

## Shapes

幾何規則以窄邊框、俐落直角區塊與少量小圓角互補。圓角只用在按鈕與狀態籤，避免整頁都變成柔軟卡片。分隔線與欄位邊界保留明確秩序，對應鉛字、摺頁與城市網格感。

## Components

全站共用導覽連結、主按鈕、狀態籤與頁面容器 token。活動條目使用開放式列表組成，不在 frontmatter 強塞邊框、欄寬、表格線等不支援欄位；這些規則由正文說明並在 runtime CSS 實作。活動記錄在桌機為多欄編排，在手機改成單欄摘要，但維持相同資料順序與唯一記錄身分。

## Do's and Don'ts

- Do 用同一套 token 管理紙感底色、墨色文字、狀態籤與導覽節奏。
- Do 讓桌機的直排詩句與橫向索引形成編輯對照，手機則改成短橫幅，不硬塞長直排。
- Don't 把活動全部做成相同卡片牆。
- Don't 把鮮色當背景主體，或用通用科技漸層取代內容層級。
