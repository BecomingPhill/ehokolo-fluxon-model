import os
import sys
import threading
import time
import socket
import pytest
import uvicorn
from playwright.sync_api import sync_playwright

def find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port

@pytest.fixture(scope="module")
def server_url():
    port = find_free_port()
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    def run_server():
        uvicorn.run("engine.server:app", host="127.0.0.1", port=port, log_level="warning")
        
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    
    # Wait for local server spin up
    time.sleep(1.5)
    yield f"http://127.0.0.1:{port}"

def test_frontend_ui(server_url):
    with sync_playwright() as p:
        # Launch headless browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Listen for console messages and page errors
        page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
        page.on("console", lambda msg: print(f"CONSOLE {msg.type}: {msg.text}"))
        
        # Load the index page
        page.goto(server_url)
        
        # Verify page title
        assert "Flux Chem Studio" in page.title()
        
        # 1. Verify Target Input and Fetch Button are visible and editable
        pdb_input = page.locator("#pdb-id-input")
        assert pdb_input.is_visible(), "PDB input box is not visible"
        assert pdb_input.is_enabled(), "PDB input box is disabled / not editable"
        pdb_input.fill("")
        pdb_input.fill("1HSG")
        assert pdb_input.input_value() == "1HSG"
        
        fetch_btn = page.locator("#fetch-target-btn")
        assert fetch_btn.is_visible()
        assert fetch_btn.is_enabled()
        
        # 2. Verify Search bar is visible and editable
        search_input = page.locator("#search-query")
        assert search_input.is_visible()
        assert search_input.is_enabled()
        search_input.fill("protease")
        assert search_input.input_value() == "protease"
        
        # 3. Verify Sliders exist and dynamically update their values
        grid_slider = page.locator("#grid-size")
        assert grid_slider.is_visible()
        assert grid_slider.is_enabled()
        
        # Slide grid resolution to 48 and verify UI label changes
        grid_slider.fill("48")
        assert page.locator("#grid-val").text_content() == "48"
        grid_slider.fill("32")
        
        # Slide box size to 24 and verify label
        box_slider = page.locator("#box-size")
        assert box_slider.is_visible()
        box_slider.fill("24")
        assert page.locator("#box-val").text_content() == "24.0"
        
        # Slide simulation steps to 800 and verify label
        steps_slider = page.locator("#sim-steps")
        assert steps_slider.is_visible()
        steps_slider.fill("800")
        assert page.locator("#steps-val").text_content() == "800"
        steps_slider.fill("300")
        
        # Slide damping (delta) to 0.35 and verify label
        damping_slider = page.locator("#damping")
        assert damping_slider.is_visible()
        damping_slider.fill("0.35")
        assert page.locator("#damping-val").text_content() == "0.35"
        
        # 4. Click Fetch PDB button and assert progress log is shown
        fetch_btn.click()
        page.wait_for_timeout(3000)  # Wait for fetch to hit RCSB PDB and complete
        
        # Target info should show target status
        info_text = page.locator("#target-info").text_content()
        assert "1HSG" in info_text or "Loaded" in info_text or "Fetching" in info_text

        # 4b. Click De Novo Evolution button and assert log and status are updated
        evo_btn = page.locator("#run-evolution-btn")
        assert evo_btn.is_visible()
        evo_btn.click()
        # Wait up to 15s for de novo simulation to finish
        page.wait_for_function(
            "document.getElementById('evolution-log').textContent.includes('Selected Scaffold:')",
            timeout=15000
        )
        assert "Step" in page.locator("#evolution-log").text_content()
        assert page.locator("#score-delta").text_content() != "-"


        # 5. Verify Science Guide Modal toggling
        guide_btn = page.locator("#toggle-guide-btn")
        assert guide_btn.is_visible()
        assert guide_btn.is_enabled()
        
        modal = page.locator("#science-guide-modal")
        # Initially, the modal should have the "hidden" class or not be visible
        assert "hidden" in modal.get_attribute("class")
        
        # Click the button to open it
        guide_btn.click()
        page.wait_for_timeout(300)
        assert "hidden" not in modal.get_attribute("class")
        assert modal.is_visible()
        
        # Verify the translation table has some content
        table = page.locator("#science-guide-modal .translation-table")
        assert table.is_visible()
        assert "Harmonic Density State" in table.text_content()
        
        # Click the close button
        close_btn = page.locator("#close-guide-btn")
        assert close_btn.is_visible()
        close_btn.click()
        page.wait_for_timeout(300)
        assert "hidden" in modal.get_attribute("class")

        # 6. Verify presence of info-icons and tooltips
        info_icons = page.locator(".info-icon")
        assert info_icons.count() > 0
        first_icon = info_icons.first
        assert first_icon.is_visible()
        assert first_icon.get_attribute("data-tooltip") is not None

        # 7. Verify Documentation Link exists and serves correctly
        docs_link = page.locator("#nav-docs-link")
        assert docs_link.is_visible()
        assert docs_link.get_attribute("href") == "/docs.html"
        assert docs_link.get_attribute("target") == "_blank"
        
        # Open docs directly and verify content loads
        page.goto(server_url + "/docs.html")
        assert "Documentation" in page.title()
        assert page.locator("h1").first.text_content() == "Understanding the Eholoko Fluxon Model (EFM)"
        assert page.locator("#link-about").is_visible()
        
        browser.close()

def test_validation_benchmark_ui(server_url):
    with sync_playwright() as p:
        # Launch headless browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Listen for console messages and page errors
        page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
        page.on("console", lambda msg: print(f"CONSOLE {msg.type}: {msg.text}"))
        
        # Open docs directly
        page.goto(server_url + "/docs.html")
        assert "Documentation" in page.title()
        
        # Verify diagnostic benchmarking elements are present
        benchmark_btn = page.locator("#run-benchmark-btn")
        assert benchmark_btn.is_visible(), "Run Benchmark button is not visible"
        assert benchmark_btn.is_enabled(), "Run Benchmark button is disabled"
        
        status_badge = page.locator("#benchmark-status")
        assert "Awaiting Verification" in status_badge.text_content()
        
        # Mock the run_validation_benchmark API call to avoid slow simulation and flakiness
        import json
        mock_response = {
            "status": "success",
            "target_pdb": "1HSG",
            "target_class": "Viral Protease",
            "calibration_used": "Class-Specific (Viral Protease)",
            "results": [
                {
                    "name": "native (1HSG - Crystal Ref)",
                    "type": "native",
                    "delta_E": -0.45,
                    "predicted_pki": 8.1,
                    "exp_pki": 8.1,
                    "exp_pki_desc": "Ki ≈ 8.0 nM (pKi = 8.10)",
                    "favorable": True,
                    "pass": True
                },
                {
                    "name": "high (1HXB - High)",
                    "type": "high",
                    "delta_E": -0.62,
                    "predicted_pki": 9.5,
                    "exp_pki": 9.1,
                    "exp_pki_desc": "Ki ≈ 1.0 nM (pKi = 9.10)",
                    "favorable": True,
                    "pass": True
                },
                {
                    "name": "med (1HEG - Med)",
                    "type": "med",
                    "delta_E": -0.32,
                    "predicted_pki": 7.2,
                    "exp_pki": 7.1,
                    "exp_pki_desc": "Ki ≈ 80.0 nM (pKi = 7.10)",
                    "favorable": True,
                    "pass": True
                },
                {
                    "name": "low (1HVI - Low)",
                    "type": "low",
                    "delta_E": -0.12,
                    "predicted_pki": 5.4,
                    "exp_pki": 5.1,
                    "exp_pki_desc": "Ki ≈ 8000.0 nM (pKi = 5.10)",
                    "favorable": True,
                    "pass": True
                },
                {
                    "name": "Steric Clash Control (Shifted Native)",
                    "type": "clash",
                    "delta_E": 0.25,
                    "predicted_pki": 2.1,
                    "exp_pki": 0.0,
                    "exp_pki_desc": "N/A (Steric Clash)",
                    "favorable": False,
                    "pass": True
                }
            ],
            "hierarchy_validated": True,
            "pearson_r": 0.95
        }
        
        page.route("**/run_validation_benchmark", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(mock_response)
        ))

        # Click the run button
        benchmark_btn.click()
        
        # Wait up to 5000ms. Since it is mocked, it should be instant.
        page.wait_for_function(
            "document.getElementById('benchmark-status').textContent.trim() === 'Verified Pass'",
            timeout=5000
        )
        
        # Verify results table is visible and populated
        results_wrapper = page.locator("#benchmark-results-wrapper")
        assert results_wrapper.is_visible()
        
        rows = page.locator("#benchmark-results-body tr")
        assert rows.count() == 5, f"Expected 5 rows in validation results, got {rows.count()}"
        
        # Check that each row has a PASS badge
        for i in range(5):
            row_text = rows.nth(i).text_content()
            assert "PASS" in row_text, f"Row {i} did not pass: {row_text}"
            
        # Verify summary box is visible and contains PASS
        summary_box = page.locator("#validation-summary-box")
        assert summary_box.is_visible()
        assert "PASS" in page.locator("#validation-summary-title").text_content()
        
        browser.close()

def test_statistical_validation_ui(server_url):
    with sync_playwright() as p:
        # Launch headless browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Listen for console messages and page errors
        page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
        page.on("console", lambda msg: print(f"CONSOLE {msg.type}: {msg.text}"))
        
        # Open docs directly
        page.goto(server_url + "/docs.html")
        assert "Documentation" in page.title()
        
        # 1. Verify statistical validation elements are present
        link = page.locator("#link-statistical")
        assert link.is_visible(), "Section 8 sidebar link is not visible"
        
        # Wait for the status badge to update to Verified Pass (loaded pre-calculated results)
        status_badge = page.locator("#stat-status")
        page.wait_for_function(
            "document.getElementById('stat-status').textContent.trim() === 'Verified Pass'",
            timeout=10000
        )
        
        # 2. Check metric cards are filled with pre-calculated results
        pearson_val = page.locator("#metric-pearson").text_content()
        assert pearson_val != "-", "Pearson value should be loaded"
        assert abs(float(pearson_val)) < 1.0, f"Unexpected Pearson value: {pearson_val}"
        
        spearman_val = page.locator("#metric-spearman").text_content()
        assert spearman_val != "-"
        
        pvalue_val = page.locator("#metric-pvalue").text_content()
        assert pvalue_val != "-"
        
        mae_val = page.locator("#metric-mae").text_content()
        assert "log units" in mae_val
        
        # 3. Check table rendering
        rows = page.locator("#stat-results-body tr")
        assert rows.count() > 0, "Expected table rows to be rendered"
        initial_count = rows.count()
        assert initial_count >= 100, f"Expected at least 100 targets, got {initial_count}"
        
        # Check search badge count text
        badge_text = page.locator("#search-count-badge").text_content()
        assert f"Showing {initial_count} / {initial_count} targets" in badge_text
        
        # 4. Test searching / filtering
        search_input = page.locator("#stat-table-search")
        search_input.fill("thrombin")
        page.wait_for_timeout(500) # wait for filtering
        
        filtered_rows = page.locator("#stat-results-body tr")
        filtered_count = filtered_rows.count()
        assert filtered_count < initial_count, f"Table should be filtered. Got {filtered_count} rows"
        
        filtered_badge_text = page.locator("#search-count-badge").text_content()
        assert f"Showing {filtered_count} / {initial_count} targets" in filtered_badge_text
        
        # Clear search
        search_input.fill("")
        page.wait_for_timeout(500)
        assert rows.count() == initial_count
        
        # 5. Mock progress and click run validation to test the interactive progress bar flow
        # Intercept POST to /run_statistical_validation
        page.route("**/run_statistical_validation", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='{"status": "running", "message": "Validation pipeline started"}'
        ))
        
        # We will mock the GET to /statistical_validation_status to simulate running progress
        progress_calls = 0
        def handle_status_route(route):
            nonlocal progress_calls
            progress_calls += 1
            if progress_calls == 1:
                # Simulate running state
                body = '{"status": "running", "progress": 35.0, "current_target": "1A30", "error_message": "", "results": null}'
            elif progress_calls == 2:
                # Simulate success state
                body = '{"status": "success", "progress": 100.0, "current_target": "Completed", "error_message": "", "results": {"summary": {"total_targets": 100, "pearson_r": 0.0288, "pearson_p": 0.7916, "spearman_rho": 0.0508, "spearman_p": 0.6413, "mae": 0.92, "regression_slope": 0.3, "regression_intercept": 8.1, "elapsed_seconds": 44.35, "class_breakdown": {}}, "results": [{"pdb_id": "181l", "target_class": "T4 Lysozyme", "ligand_name": "benzene", "exp_pki": 3.49, "E_target": 1.0, "E_complex": 1.1, "delta_E": 0.1, "time_seconds": 0.5, "pred_pki": 3.5, "residual": -0.01}]}}'
            else:
                body = '{"status": "success", "progress": 100.0, "current_target": "Completed", "error_message": "", "results": {"summary": {"total_targets": 100, "pearson_r": 0.0288, "pearson_p": 0.7916, "spearman_rho": 0.0508, "spearman_p": 0.6413, "mae": 0.92, "regression_slope": 0.3, "regression_intercept": 8.1, "elapsed_seconds": 44.35, "class_breakdown": {}}, "results": [{"pdb_id": "181l", "target_class": "T4 Lysozyme", "ligand_name": "benzene", "exp_pki": 3.49, "E_target": 1.0, "E_complex": 1.1, "delta_E": 0.1, "time_seconds": 0.5, "pred_pki": 3.5, "residual": -0.01}]}}'
            route.fulfill(status=200, content_type="application/json", body=body)
            
        page.route("**/statistical_validation_status", handle_status_route)
        
        # Click the run button
        run_btn = page.locator("#run-stat-btn")
        assert run_btn.is_enabled()
        run_btn.click()
        
        # Wait for the status to show running
        page.wait_for_function(
            "document.getElementById('stat-status').textContent.includes('Running')",
            timeout=5000
        )
        
        # Wait for the status to become success (Verified Pass)
        page.wait_for_function(
            "document.getElementById('stat-status').textContent.trim() === 'Verified Pass'",
            timeout=5000
        )
        
        # Check that the progress container is hidden
        assert not page.locator("#stat-progress-container").is_visible()
        
        browser.close()

def test_docking_calibration_ui(server_url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
        page.on("console", lambda msg: print(f"CONSOLE {msg.type}: {msg.text}"))
        
        page.goto(server_url)
        
        # Wait for the default load of 1HSG to finish
        page.wait_for_function(
            "document.getElementById('target-info').textContent.includes('PDB 1HSG')",
            timeout=10000
        )
        
        # 1. Verify target-class-select exists
        select = page.locator("#target-class-select")
        assert select.is_visible()
        assert select.input_value() == "Viral Protease"
        
        # 2. Change target class to DHFR
        select.select_option("DHFR")
        assert select.input_value() == "DHFR"
        
        # 3. Intercept run_screening API request
        captured_request_body = {}
        def handle_run_screening(route):
            nonlocal captured_request_body
            req = route.request
            import json
            captured_request_body = json.loads(req.post_data)
            response_body = {
                "E_target": 1.5,
                "E_complex": 1.2,
                "delta_E": -0.3,
                "is_favorable": True,
                "center": [0.0, 0.0, 0.0],
                "predicted_pki": 8.45,
                "calibration_used": "Class-Specific (DHFR)"
            }
            route.fulfill(status=200, content_type="application/json", body=json.dumps(response_body))
            
        page.route("**/run_screening", handle_run_screening)
        
        # 4. Set targetAtoms and ligandAtoms in frontend context to mock loaded target and ligand
        page.evaluate("targetAtoms = [{element: 'C', x: 0.0, y: 0.0, z: 0.0}]; ligandAtoms = [{element: 'C', x: 1.0, y: 1.0, z: 1.0}];")
        
        # 5. Click the Run EFM Docking button
        run_btn = page.locator("#run-docking-btn")
        assert run_btn.is_visible()
        run_btn.click()
        
        # 6. Wait for score updates in UI
        page.wait_for_timeout(500)
        
        # 7. Check if request body contains target_class: "DHFR"
        assert captured_request_body.get("target_class") == "DHFR"
        
        # 8. Check that E_target, E_complex, delta_E, and score-pki are rendered in UI
        assert page.locator("#score-ea").text_content() == "1.5000"
        assert page.locator("#score-eab").text_content() == "1.2000"
        assert page.locator("#score-delta").text_content() == "-0.3000"
        assert page.locator("#score-pki").text_content() == "8.45"
        
        # 9. Check the status banner text
        status_text = page.locator("#binding-status").text_content()
        assert "pKi = 8.45" in status_text
        assert "Class-Specific (DHFR)" in status_text
        
        browser.close()

def test_target_class_autodetect_ui(server_url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
        page.on("console", lambda msg: print(f"CONSOLE {msg.type}: {msg.text}"))
        
        page.goto(server_url)
        
        # Wait for the DOMContentLoaded default fetch of 1HSG to finish
        page.wait_for_function(
            "document.getElementById('target-info').textContent.includes('PDB 1HSG')",
            timeout=10000
        )
        
        # Assert target-class-select value is "Viral Protease"
        select = page.locator("#target-class-select")
        assert select.input_value() == "Viral Protease"
        
        browser.close()

def test_state_reset_ui(server_url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
        page.on("console", lambda msg: print(f"CONSOLE {msg.type}: {msg.text}"))
        
        page.goto(server_url)
        
        # Wait for 1HSG to be loaded (default load on DOMContentLoaded)
        page.wait_for_function(
            "document.getElementById('target-info').textContent.includes('PDB 1HSG')",
            timeout=10000
        )
        
        # Mock running screening to populate scores
        page.evaluate("targetAtoms = [{element: 'C', x: 0.0, y: 0.0, z: 0.0}]; ligandAtoms = [{element: 'C', x: 1.0, y: 1.0, z: 1.0}];")
        
        # Intercept run_screening API request
        page.route("**/run_screening", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='{"E_target": 1.5, "E_complex": 1.2, "delta_E": -0.3, "is_favorable": true, "center": [0.0, 0.0, 0.0], "predicted_pki": 8.45, "calibration_used": "Class-Specific (Viral Protease)"}'
        ))
        
        page.locator("#run-docking-btn").click()
        page.wait_for_timeout(500)
        
        # Check that scores are populated
        assert page.locator("#score-ea").text_content() == "1.5000"
        assert page.locator("#export-results-btn").is_enabled()
        
        # Click clear button (confirming the dialog)
        page.on("dialog", lambda dialog: dialog.accept())
        page.locator("#clear-all-btn").click()
        page.wait_for_timeout(200)
        
        # Check that target info is reset
        assert "No target protein loaded." in page.locator("#target-info").text_content()
        assert page.locator("#score-ea").text_content() == "-"
        assert page.locator("#export-results-btn").is_disabled()
        
        browser.close()

def test_docking_without_ligand_shows_alert(server_url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
        page.on("console", lambda msg: print(f"CONSOLE {msg.type}: {msg.text}"))
        
        page.goto(server_url)
        
        # Wait for default load of 1HSG
        page.wait_for_function(
            "document.getElementById('target-info').textContent.includes('PDB 1HSG')",
            timeout=10000
        )
        
        # Clear ligand atoms explicitly
        page.evaluate("ligandAtoms = []")
        
        # Click Run EFM Docking, catch the alert
        alert_msg = ""
        def handle_dialog(dialog):
            nonlocal alert_msg
            alert_msg = dialog.message
            dialog.accept()
            
        page.on("dialog", handle_dialog)
        page.locator("#run-docking-btn").click()
        page.wait_for_timeout(500)
        
        assert "Please load a compound / ligand first" in alert_msg
        
        browser.close()

