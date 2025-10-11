#!/usr/bin/env python3
"""
HTML Export Handler

Handles the generation of HTML files with embedded CSS and JavaScript for test results.
Provides comprehensive data export with interactive features and professional styling.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class HTMLExporter:
    """
    HTML export handler for test results and data.
    
    This class provides comprehensive HTML export functionality with:
    - Professional styling with embedded CSS
    - Interactive features with embedded JavaScript
    - Responsive design
    - Data visualization
    - Easy-to-read formatting
    """
    
    def __init__(self, output_directory: str = "./output/reports"):
        """
        Initialize HTML exporter.
        
        Args:
            output_directory (str): Directory to save HTML files
        """
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def export_test_results(self, test_summary: Dict[str, Any], 
                          cycle_data: List[Dict[str, Any]] = None,
                          uart_data: List[Dict[str, Any]] = None,
                          validation_results: List[Dict[str, Any]] = None,
                          filename_prefix: str = "test_results") -> str:
        """
        Export comprehensive test results to HTML format.
        
        Args:
            test_summary (dict): Overall test summary data
            cycle_data (list): Individual cycle execution data
            uart_data (list): UART data collected during tests
            validation_results (list): Pattern validation results
            filename_prefix (str): Prefix for the generated filename
            
        Returns:
            str: Path to the generated HTML file
        """
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f"{filename_prefix}_{timestamp}.html"
        filepath = self.output_directory / filename
        
        self.logger.info(f"Exporting test results to HTML: {filepath}")
        
        try:
            # Generate HTML content
            html_content = self._generate_html_content(
                test_summary, cycle_data, uart_data, validation_results
            )
            
            # Write HTML file
            with open(filepath, 'w', encoding='utf-8') as htmlfile:
                htmlfile.write(html_content)
            
            self.logger.info(f"HTML export completed successfully: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Failed to export HTML: {e}")
            raise
    
    def _generate_html_content(self, test_summary: Dict[str, Any], 
                             cycle_data: List[Dict[str, Any]] = None,
                             uart_data: List[Dict[str, Any]] = None,
                             validation_results: List[Dict[str, Any]] = None) -> str:
        """Generate complete HTML content."""
        html_parts = [
            self._get_html_header(),
            self._get_css_styles(),
            self._get_html_body_start(),
            self._get_navigation(),
            self._get_summary_section(test_summary),
            self._get_statistics_section(test_summary, cycle_data, validation_results),
            self._get_cycle_data_section(cycle_data),
            self._get_uart_data_section(uart_data),
            self._get_validation_section(validation_results),
            self._get_footer_section(),
            self._get_javascript(),
            self._get_html_body_end()
        ]
        
        return '\n'.join(html_parts)
    
    def _get_html_header(self) -> str:
        """Get HTML document header."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Results - Automated Power Cycle and UART Validation Framework</title>
    <meta name="description" content="Comprehensive test results from the Automated Power Cycle and UART Validation Framework">
    <meta name="generator" content="Automated Power Cycle and UART Validation Framework v1.0.0">"""
    
    def _get_css_styles(self) -> str:
        """Get embedded CSS styles."""
        return """
    <style>
        /* Reset and base styles */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f8f9fa;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* Header styles */
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem 0;
            text-align: center;
            margin-bottom: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            font-weight: 300;
        }
        
        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        /* Navigation styles */
        .nav {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            margin-bottom: 2rem;
        }
        
        .nav ul {
            list-style: none;
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
        }
        
        .nav a {
            color: #667eea;
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            transition: background-color 0.3s;
        }
        
        .nav a:hover {
            background-color: #f0f2ff;
        }
        
        /* Section styles */
        .section {
            background: white;
            margin-bottom: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        
        .section-header {
            background: #f8f9fa;
            padding: 1rem 1.5rem;
            border-bottom: 1px solid #dee2e6;
            font-size: 1.3rem;
            font-weight: 600;
            color: #495057;
        }
        
        .section-content {
            padding: 1.5rem;
        }
        
        /* Summary cards */
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .summary-card {
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            text-align: center;
            transition: transform 0.3s;
        }
        
        .summary-card:hover {
            transform: translateY(-2px);
        }
        
        .summary-card h3 {
            color: #667eea;
            margin-bottom: 0.5rem;
            font-size: 1.1rem;
        }
        
        .summary-card .value {
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        
        .summary-card .label {
            color: #6c757d;
            font-size: 0.9rem;
        }
        
        /* Status badges */
        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .status-pass {
            background-color: #d4edda;
            color: #155724;
        }
        
        .status-fail {
            background-color: #f8d7da;
            color: #721c24;
        }
        
        .status-partial {
            background-color: #fff3cd;
            color: #856404;
        }
        
        .status-error {
            background-color: #f8d7da;
            color: #721c24;
        }
        
        /* Table styles */
        .table-container {
            overflow-x: auto;
            margin-top: 1rem;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
        }
        
        th, td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }
        
        th {
            background-color: #f8f9fa;
            font-weight: 600;
            color: #495057;
        }
        
        tr:hover {
            background-color: #f8f9fa;
        }
        
        /* Chart container */
        .chart-container {
            margin: 2rem 0;
            padding: 1rem;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .chart {
            width: 100%;
            height: 300px;
            background: #f8f9fa;
            border-radius: 5px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #6c757d;
        }
        
        /* Collapsible sections */
        .collapsible {
            cursor: pointer;
            user-select: none;
        }
        
        .collapsible::after {
            content: '▼';
            float: right;
            transition: transform 0.3s;
        }
        
        .collapsible.active::after {
            transform: rotate(180deg);
        }
        
        .collapsible-content {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
        }
        
        .collapsible-content.active {
            max-height: 1000px;
        }
        
        /* Footer styles */
        .footer {
            background: #343a40;
            color: white;
            text-align: center;
            padding: 2rem;
            margin-top: 3rem;
            border-radius: 8px;
        }
        
        .footer p {
            margin-bottom: 0.5rem;
        }
        
        .footer a {
            color: #667eea;
            text-decoration: none;
        }
        
        .footer a:hover {
            text-decoration: underline;
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .nav ul {
                flex-direction: column;
            }
            
            .summary-grid {
                grid-template-columns: 1fr;
            }
            
            .table-container {
                font-size: 0.9rem;
            }
        }
        
        /* Print styles */
        @media print {
            body {
                background: white;
            }
            
            .header {
                background: #667eea !important;
                -webkit-print-color-adjust: exact;
            }
            
            .section {
                box-shadow: none;
                border: 1px solid #dee2e6;
            }
            
            .nav {
                display: none;
            }
        }
    </style>"""
    
    def _get_html_body_start(self) -> str:
        """Get HTML body start."""
        return """
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔬 Test Results Report</h1>
            <p>Automated Power Cycle and UART Validation Framework</p>
            <p>Generated: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
        </div>"""
    
    def _get_navigation(self) -> str:
        """Get navigation section."""
        return """
        <nav class="nav">
            <ul>
                <li><a href="#summary">📊 Summary</a></li>
                <li><a href="#statistics">📈 Statistics</a></li>
                <li><a href="#cycles">🔄 Cycles</a></li>
                <li><a href="#uart">📡 UART Data</a></li>
                <li><a href="#validation">✅ Validation</a></li>
            </ul>
        </nav>"""
    
    def _get_summary_section(self, test_summary: Dict[str, Any]) -> str:
        """Get summary section."""
        status_class = f"status-{test_summary.get('status', 'unknown').lower()}"
        success_rate = test_summary.get('success_rate', 0) * 100
        
        return f"""
        <section id="summary" class="section">
            <div class="section-header">📊 Test Summary</div>
            <div class="section-content">
                <div class="summary-grid">
                    <div class="summary-card">
                        <h3>Test Name</h3>
                        <div class="value">{test_summary.get('test_name', 'N/A')}</div>
                    </div>
                    <div class="summary-card">
                        <h3>Status</h3>
                        <div class="value">
                            <span class="status-badge {status_class}">{test_summary.get('status', 'UNKNOWN')}</span>
                        </div>
                    </div>
                    <div class="summary-card">
                        <h3>Success Rate</h3>
                        <div class="value">{success_rate:.1f}%</div>
                    </div>
                    <div class="summary-card">
                        <h3>Total Cycles</h3>
                        <div class="value">{test_summary.get('total_cycles', 0)}</div>
                    </div>
                    <div class="summary-card">
                        <h3>Successful Cycles</h3>
                        <div class="value">{test_summary.get('successful_cycles', 0)}</div>
                    </div>
                    <div class="summary-card">
                        <h3>Failed Cycles</h3>
                        <div class="value">{test_summary.get('failed_cycles', 0)}</div>
                    </div>
                    <div class="summary-card">
                        <h3>Duration</h3>
                        <div class="value">{test_summary.get('duration', 0):.1f}s</div>
                    </div>
                    <div class="summary-card">
                        <h3>Start Time</h3>
                        <div class="value">{test_summary.get('start_time', 'N/A')}</div>
                    </div>
                </div>
            </div>
        </section>"""
    
    def _get_statistics_section(self, test_summary: Dict[str, Any], 
                               cycle_data: List[Dict[str, Any]] = None,
                               validation_results: List[Dict[str, Any]] = None) -> str:
        """Get statistics section."""
        return f"""
        <section id="statistics" class="section">
            <div class="section-header collapsible">📈 Statistics & Charts</div>
            <div class="section-content collapsible-content">
                <div class="chart-container">
                    <h3>Cycle Success Rate</h3>
                    <div class="chart" id="successChart">
                        <canvas id="successCanvas" width="400" height="200"></canvas>
                    </div>
                </div>
                <div class="chart-container">
                    <h3>Cycle Duration Trend</h3>
                    <div class="chart" id="durationChart">
                        <canvas id="durationCanvas" width="400" height="200"></canvas>
                    </div>
                </div>
            </div>
        </section>"""
    
    def _get_cycle_data_section(self, cycle_data: List[Dict[str, Any]] = None) -> str:
        """Get cycle data section."""
        if not cycle_data:
            return """
        <section id="cycles" class="section">
            <div class="section-header">🔄 Cycle Data</div>
            <div class="section-content">
                <p>No cycle data available.</p>
            </div>
        </section>"""
        
        table_rows = []
        for cycle in cycle_data:
            status_class = f"status-{cycle.get('status', 'unknown').lower()}"
            table_rows.append(f"""
                <tr>
                    <td>{cycle.get('cycle_number', 'N/A')}</td>
                    <td>{cycle.get('start_time', 'N/A')}</td>
                    <td>{cycle.get('end_time', 'N/A')}</td>
                    <td>{cycle.get('duration', 0):.2f}s</td>
                    <td><span class="status-badge {status_class}">{cycle.get('status', 'UNKNOWN')}</span></td>
                    <td>{cycle.get('on_time', 'N/A')}s</td>
                    <td>{cycle.get('off_time', 'N/A')}s</td>
                    <td>{cycle.get('voltage_setting', 'N/A')}V</td>
                    <td>{cycle.get('voltage_measured', 'N/A')}V</td>
                    <td>{cycle.get('error_message', '')}</td>
                </tr>""")
        
        return f"""
        <section id="cycles" class="section">
            <div class="section-header collapsible">🔄 Cycle Data ({len(cycle_data)} cycles)</div>
            <div class="section-content collapsible-content">
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Cycle</th>
                                <th>Start Time</th>
                                <th>End Time</th>
                                <th>Duration</th>
                                <th>Status</th>
                                <th>On Time</th>
                                <th>Off Time</th>
                                <th>Voltage Set</th>
                                <th>Voltage Measured</th>
                                <th>Error</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(table_rows)}
                        </tbody>
                    </table>
                </div>
            </div>
        </section>"""
    
    def _get_uart_data_section(self, uart_data: List[Dict[str, Any]] = None) -> str:
        """Get UART data section."""
        if not uart_data:
            return """
        <section id="uart" class="section">
            <div class="section-header">📡 UART Data</div>
            <div class="section-content">
                <p>No UART data available.</p>
            </div>
        </section>"""
        
        # Limit display to first 100 entries for performance
        display_data = uart_data[:100]
        table_rows = []
        
        for data in display_data:
            data_preview = str(data.get('data', ''))[:50] + '...' if len(str(data.get('data', ''))) > 50 else str(data.get('data', ''))
            table_rows.append(f"""
                <tr>
                    <td>{data.get('timestamp', 'N/A')}</td>
                    <td>{data.get('port', 'N/A')}</td>
                    <td>{data.get('baud_rate', 'N/A')}</td>
                    <td>{len(str(data.get('data', '')))}</td>
                    <td>{data_preview}</td>
                </tr>""")
        
        more_entries = f"<p><em>Showing first 100 entries. Total entries: {len(uart_data)}</em></p>" if len(uart_data) > 100 else ""
        
        return f"""
        <section id="uart" class="section">
            <div class="section-header collapsible">📡 UART Data ({len(uart_data)} entries)</div>
            <div class="section-content collapsible-content">
                {more_entries}
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Timestamp</th>
                                <th>Port</th>
                                <th>Baud Rate</th>
                                <th>Data Length</th>
                                <th>Data Preview</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(table_rows)}
                        </tbody>
                    </table>
                </div>
            </div>
        </section>"""
    
    def _get_validation_section(self, validation_results: List[Dict[str, Any]] = None) -> str:
        """Get validation results section."""
        if not validation_results:
            return """
        <section id="validation" class="section">
            <div class="section-header">✅ Validation Results</div>
            <div class="section-content">
                <p>No validation results available.</p>
            </div>
        </section>"""
        
        table_rows = []
        for result in validation_results:
            status_class = "status-pass" if result.get('success', False) else "status-fail"
            status_text = "PASS" if result.get('success', False) else "FAIL"
            
            table_rows.append(f"""
                <tr>
                    <td>{result.get('pattern_name', 'N/A')}</td>
                    <td>{result.get('pattern_type', 'N/A')}</td>
                    <td><span class="status-badge {status_class}">{status_text}</span></td>
                    <td>{result.get('matched_data', '')}</td>
                    <td>{result.get('expected', '')}</td>
                    <td>{result.get('message', '')}</td>
                    <td>{result.get('timestamp', 'N/A')}</td>
                </tr>""")
        
        return f"""
        <section id="validation" class="section">
            <div class="section-header collapsible">✅ Validation Results ({len(validation_results)} patterns)</div>
            <div class="section-content collapsible-content">
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Pattern Name</th>
                                <th>Pattern Type</th>
                                <th>Result</th>
                                <th>Matched Data</th>
                                <th>Expected</th>
                                <th>Message</th>
                                <th>Timestamp</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(table_rows)}
                        </tbody>
                    </table>
                </div>
            </div>
        </section>"""
    
    def _get_footer_section(self) -> str:
        """Get footer section."""
        return """
        <footer class="footer">
            <p><strong>Automated Power Cycle and UART Validation Framework</strong></p>
            <p>Generated on """ + datetime.now().strftime('%Y-%m-%d at %H:%M:%S') + """</p>
            <p>Framework Version 1.0.0 | <a href="#" onclick="window.print()">Print Report</a></p>
        </footer>"""
    
    def _get_javascript(self) -> str:
        """Get embedded JavaScript."""
        return """
    <script>
        // Collapsible sections functionality
        document.addEventListener('DOMContentLoaded', function() {
            const collapsibles = document.querySelectorAll('.collapsible');
            
            collapsibles.forEach(collapsible => {
                collapsible.addEventListener('click', function() {
                    this.classList.toggle('active');
                    const content = this.nextElementSibling;
                    content.classList.toggle('active');
                });
            });
            
            // Smooth scrolling for navigation links
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', function (e) {
                    e.preventDefault();
                    const target = document.querySelector(this.getAttribute('href'));
                    if (target) {
                        target.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start'
                        });
                    }
                });
            });
            
            // Simple chart drawing
            drawCharts();
        });
        
        function drawCharts() {
            // Success rate chart
            const successCanvas = document.getElementById('successCanvas');
            if (successCanvas) {
                const ctx = successCanvas.getContext('2d');
                drawSuccessChart(ctx);
            }
            
            // Duration trend chart
            const durationCanvas = document.getElementById('durationCanvas');
            if (durationCanvas) {
                const ctx = durationCanvas.getContext('2d');
                drawDurationChart(ctx);
            }
        }
        
        function drawSuccessChart(ctx) {
            const canvas = ctx.canvas;
            const width = canvas.width;
            const height = canvas.height;
            
            // Get success rate from page data
            const successRate = parseFloat(document.querySelector('.summary-card:nth-child(3) .value').textContent);
            
            // Draw pie chart
            const centerX = width / 2;
            const centerY = height / 2;
            const radius = Math.min(width, height) / 2 - 20;
            
            // Success portion
            const successAngle = (successRate / 100) * 2 * Math.PI;
            
            ctx.beginPath();
            ctx.arc(centerX, centerY, radius, 0, successAngle);
            ctx.lineTo(centerX, centerY);
            ctx.fillStyle = '#28a745';
            ctx.fill();
            
            // Failure portion
            ctx.beginPath();
            ctx.arc(centerX, centerY, radius, successAngle, 2 * Math.PI);
            ctx.lineTo(centerX, centerY);
            ctx.fillStyle = '#dc3545';
            ctx.fill();
            
            // Add labels
            ctx.fillStyle = '#333';
            ctx.font = '14px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(`${successRate.toFixed(1)}% Success`, centerX, centerY - 10);
            ctx.fillText(`${(100 - successRate).toFixed(1)}% Failed`, centerX, centerY + 10);
        }
        
        function drawDurationChart(ctx) {
            const canvas = ctx.canvas;
            const width = canvas.width;
            const height = canvas.height;
            
            // Get cycle durations from table
            const durationCells = document.querySelectorAll('#cycles tbody td:nth-child(4)');
            const durations = Array.from(durationCells).map(cell => 
                parseFloat(cell.textContent.replace('s', ''))
            );
            
            if (durations.length === 0) {
                ctx.fillStyle = '#6c757d';
                ctx.font = '16px Arial';
                ctx.textAlign = 'center';
                ctx.fillText('No duration data available', width / 2, height / 2);
                return;
            }
            
            // Draw line chart
            const padding = 40;
            const chartWidth = width - 2 * padding;
            const chartHeight = height - 2 * padding;
            
            const maxDuration = Math.max(...durations);
            const minDuration = Math.min(...durations);
            const range = maxDuration - minDuration || 1;
            
            ctx.strokeStyle = '#667eea';
            ctx.lineWidth = 2;
            ctx.beginPath();
            
            durations.forEach((duration, index) => {
                const x = padding + (index / (durations.length - 1)) * chartWidth;
                const y = padding + chartHeight - ((duration - minDuration) / range) * chartHeight;
                
                if (index === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            });
            
            ctx.stroke();
            
            // Add axis labels
            ctx.fillStyle = '#6c757d';
            ctx.font = '12px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('Cycle Duration Trend', width / 2, 20);
            
            // Add data points
            ctx.fillStyle = '#667eea';
            durations.forEach((duration, index) => {
                const x = padding + (index / (durations.length - 1)) * chartWidth;
                const y = padding + chartHeight - ((duration - minDuration) / range) * chartHeight;
                
                ctx.beginPath();
                ctx.arc(x, y, 4, 0, 2 * Math.PI);
                ctx.fill();
            });
        }
        
        // Print functionality
        function printReport() {
            window.print();
        }
        
        // Export functionality (placeholder)
        function exportData(format) {
            alert(`Export to ${format} functionality would be implemented here.`);
        }
    </script>"""
    
    def _get_html_body_end(self) -> str:
        """Get HTML body end."""
        return """
    </div>
</body>
</html>"""
    
    def export_simple_data(self, data: List[Dict[str, Any]], 
                          filename: str = "data_export.html",
                          title: str = "Data Export") -> str:
        """
        Export simple data to HTML format.
        
        Args:
            data (list): List of dictionaries to export
            filename (str): Output filename
            title (str): Page title
            
        Returns:
            str: Path to the generated HTML file
        """
        filepath = self.output_directory / filename
        
        self.logger.info(f"Exporting simple data to HTML: {filepath}")
        
        try:
            html_content = self._generate_simple_html_content(data, title)
            
            with open(filepath, 'w', encoding='utf-8') as htmlfile:
                htmlfile.write(html_content)
            
            self.logger.info(f"Simple HTML export completed: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Failed to export simple HTML: {e}")
            raise
    
    def _generate_simple_html_content(self, data: List[Dict[str, Any]], title: str) -> str:
        """Generate simple HTML content for data export."""
        if not data:
            table_content = "<p>No data available.</p>"
        else:
            # Generate table headers
            headers = list(data[0].keys())
            header_row = '<tr>' + ''.join(f'<th>{header}</th>' for header in headers) + '</tr>'
            
            # Generate table rows
            data_rows = []
            for row in data:
                row_cells = ''.join(f'<td>{row.get(header, "N/A")}</td>' for header in headers)
                data_rows.append(f'<tr>{row_cells}</tr>')
            
            table_content = f"""
            <div class="table-container">
                <table>
                    <thead>{header_row}</thead>
                    <tbody>{''.join(data_rows)}</tbody>
                </table>
            </div>"""
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {self._get_css_styles()}
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <section class="section">
            <div class="section-header">Data Export ({len(data)} records)</div>
            <div class="section-content">
                {table_content}
            </div>
        </section>
        
        <footer class="footer">
            <p><strong>Automated Power Cycle and UART Validation Framework</strong></p>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}</p>
        </footer>
    </div>
    
    {self._get_javascript()}
</body>
</html>"""


# Example usage
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create exporter
    exporter = HTMLExporter()
    
    # Sample test data
    test_summary = {
        'test_name': 'Sample Test',
        'start_time': '2024-01-15 10:00:00',
        'end_time': '2024-01-15 10:05:00',
        'duration': 300,
        'total_cycles': 3,
        'successful_cycles': 2,
        'failed_cycles': 1,
        'success_rate': 0.67,
        'status': 'PARTIAL'
    }
    
    cycle_data = [
        {
            'cycle_number': 1,
            'start_time': '2024-01-15 10:00:00',
            'end_time': '2024-01-15 10:01:00',
            'duration': 60,
            'status': 'PASS',
            'on_time': 30,
            'off_time': 30,
            'voltage_setting': 5.0,
            'voltage_measured': 4.98
        },
        {
            'cycle_number': 2,
            'start_time': '2024-01-15 10:01:00',
            'end_time': '2024-01-15 10:02:00',
            'duration': 60,
            'status': 'PASS',
            'on_time': 30,
            'off_time': 30,
            'voltage_setting': 5.0,
            'voltage_measured': 5.01
        },
        {
            'cycle_number': 3,
            'start_time': '2024-01-15 10:02:00',
            'end_time': '2024-01-15 10:03:00',
            'duration': 60,
            'status': 'FAIL',
            'on_time': 30,
            'off_time': 30,
            'voltage_setting': 5.0,
            'voltage_measured': 0.0,
            'error_message': 'Power supply communication error'
        }
    ]
    
    validation_results = [
        {
            'pattern_name': 'boot_ready',
            'pattern_type': 'regex',
            'success': True,
            'matched_data': 'READY',
            'expected': 'READY',
            'message': 'Pattern matched successfully',
            'timestamp': '2024-01-15 10:00:30'
        },
        {
            'pattern_name': 'voltage_check',
            'pattern_type': 'numeric_range',
            'success': False,
            'matched_data': '0.0',
            'expected': '4.8-5.2',
            'message': 'Voltage out of range',
            'timestamp': '2024-01-15 10:02:30'
        }
    ]
    
    # Export test results
    html_file = exporter.export_test_results(test_summary, cycle_data, None, validation_results)
    print(f"HTML export completed: {html_file}")
    
    # Export simple data
    simple_file = exporter.export_simple_data(cycle_data, "simple_cycles.html", "Cycle Data Export")
    print(f"Simple HTML export completed: {simple_file}")
