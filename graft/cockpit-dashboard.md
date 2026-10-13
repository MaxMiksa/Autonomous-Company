---
name: Cockpit Dashboard
slug: cockpit-dashboard
type: system
sources:
  - path: dashboard/app.js
    hash: 1a974b1c1d72cf714de69954e840a6335990788860f9442ad1e61fcf6f041ca8
sources_digest: 8a02818c5dd3a3db3dd230d982a76cda1e4dfe081bb76b6e106dc18b660fa0ae
links:
  - to: cockpit-dashboard-server
    relation: uses
    description: >-
      Polls /api/status, /api/hold, /api/directive, /api/ideas, /api/tool-usage
      REST endpoints served by the dashboard server.
generator:
  version: 1
covers:
  - symbol: escapeHtml
    kind: function
    at: 'dashboard/app.js:L92-L99'
  - symbol: renderInlineMarkdown
    kind: function
    at: 'dashboard/app.js:L101-L108'
  - symbol: renderMarkdown
    kind: function
    at: 'dashboard/app.js:L110-L192'
  - symbol: closeParagraph
    kind: function
    at: 'dashboard/app.js:L117-L122'
  - symbol: closeList
    kind: function
    at: 'dashboard/app.js:L123-L128'
  - symbol: classForState
    kind: function
    at: 'dashboard/app.js:L194-L216'
  - symbol: applyCardState
    kind: function
    at: 'dashboard/app.js:L218-L221'
  - symbol: renderGraft
    kind: function
    at: 'dashboard/app.js:L223-L246'
  - symbol: formatTime
    kind: function
    at: 'dashboard/app.js:L248-L254'
  - symbol: renderStateList
    kind: function
    at: 'dashboard/app.js:L256-L285'
  - symbol: ladder
    kind: function
    at: 'dashboard/app.js:L262-L262'
  - symbol: fetchStatus
    kind: function
    at: 'dashboard/app.js:L287-L348'
  - symbol: renderCost
    kind: function
    at: 'dashboard/app.js:L350-L398'
  - symbol: usd
    kind: function
    at: 'dashboard/app.js:L351-L351'
  - symbol: renderCcusage
    kind: function
    at: 'dashboard/app.js:L400-L420'
  - symbol: usd
    kind: function
    at: 'dashboard/app.js:L402-L402'
  - symbol: renderHold
    kind: function
    at: 'dashboard/app.js:L426-L436'
  - symbol: setHold
    kind: function
    at: 'dashboard/app.js:L438-L468'
  - symbol: renderDirective
    kind: function
    at: 'dashboard/app.js:L470-L485'
  - symbol: submitDirective
    kind: function
    at: 'dashboard/app.js:L487-L530'
  - symbol: send
    kind: function
    at: 'dashboard/app.js:L498-L503'
  - symbol: renderSettings
    kind: function
    at: 'dashboard/app.js:L532-L552'
  - symbol: gatherSettings
    kind: function
    at: 'dashboard/app.js:L554-L561'
  - symbol: loadIdeas
    kind: function
    at: 'dashboard/app.js:L564-L584'
  - symbol: loadToolUsage
    kind: function
    at: 'dashboard/app.js:L587-L622'
  - symbol: loadAnalysis
    kind: function
    at: 'dashboard/app.js:L626-L650'
  - symbol: renderAnalystTrigger
    kind: function
    at: 'dashboard/app.js:L654-L667'
  - symbol: runAnalystNow
    kind: function
    at: 'dashboard/app.js:L669-L686'
  - symbol: extractDirective
    kind: function
    at: 'dashboard/app.js:L692-L704'
  - symbol: copyToBtn
    kind: function
    at: 'dashboard/app.js:L706-L714'
  - symbol: loadDirectiveTemplates
    kind: function
    at: 'dashboard/app.js:L728-L760'
  - symbol: loadSettings
    kind: function
    at: 'dashboard/app.js:L763-L771'
  - symbol: saveSettings
    kind: function
    at: 'dashboard/app.js:L773-L802'
  - symbol: setWakeAvailability
    kind: function
    at: 'dashboard/app.js:L808-L815'
  - symbol: wakeLoop
    kind: function
    at: 'dashboard/app.js:L817-L834'
  - symbol: resetAutoTimer
    kind: function
    at: 'dashboard/app.js:L837-L850'
  - symbol: notifiedIds
    kind: function
    at: 'dashboard/app.js:L926-L933'
  - symbol: rememberNotified
    kind: function
    at: 'dashboard/app.js:L935-L942'
  - symbol: renderNotifyButton
    kind: function
    at: 'dashboard/app.js:L944-L962'
  - symbol: announceNewRequests
    kind: function
    at: 'dashboard/app.js:L964-L984'
  - symbol: opreqPanelBusy
    kind: function
    at: 'dashboard/app.js:L992-L999'
  - symbol: renderOperatorRequests
    kind: function
    at: 'dashboard/app.js:L1001-L1060'
  - symbol: submitDecision
    kind: function
    at: 'dashboard/app.js:L1062-L1101'
  - symbol: loadOperatorRequests
    kind: function
    at: 'dashboard/app.js:L1103-L1110'
---
<!-- context:generated:start -->
## Summary

Browser-side single-page monitoring/control panel for the autonomous agent loop. Polls /api/status on a timer, renders live state cards (guardian, systemd daemon, loop, autostart, graft freshness), cost/usage panels, a directive editor, settings form, and log/consensus views. The only real loop control is setHold (replacing container no-op Start/Stop); submitDirective has a deliberate allowPending retry flow to override a live PENDING directive. Hand-rolled dependency-free markdown rendering; consensus panel refuses to overwrite while operator reads the full file; credit badge treats out_of_credits as informational 'SUBSCRIPTION ONLY'; ccusage block fails open. UI strings mixed Turkish/English; all state via REST endpoints with no external libraries.

## Related

- uses [[cockpit-dashboard-server]] — Polls /api/status, /api/hold, /api/directive, /api/ideas, /api/tool-usage REST endpoints served by the dashboard server.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
