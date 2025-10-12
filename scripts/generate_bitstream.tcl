#!/usr/bin/env tclsh
# Xilinx Generate Bitstream TCL Script
# This script generates a bitstream for a Vivado project
# Usage: vivado -mode batch -source generate_bitstream.tcl -tclargs <project_path> [output_dir] [jobs]

# Set default values
set project_path ""
set output_dir "./bitstreams"
set jobs 4
set run_synthesis true
set run_implementation true
set generate_bitstream true
set verbose false

# Parse command line arguments
if {[llength $argv] >= 1} {
    set project_path [lindex $argv 0]
}

if {[llength $argv] >= 2} {
    set output_dir [lindex $argv 1]
}

if {[llength $argv] >= 3} {
    set jobs [lindex $argv 2]
}

if {[llength $argv] >= 4} {
    set run_synthesis [lindex $argv 3]
}

if {[llength $argv] >= 5} {
    set run_implementation [lindex $argv 4]
}

if {[llength $argv] >= 6} {
    set generate_bitstream [lindex $argv 5]
}

if {[llength $argv] >= 7} {
    set verbose [lindex $argv 6]
}

puts "=== Xilinx Generate Bitstream Script ==="
puts "Project Path: $project_path"
puts "Output Directory: $output_dir"
puts "Jobs: $jobs"
puts "Run Synthesis: $run_synthesis"
puts "Run Implementation: $run_implementation"
puts "Generate Bitstream: $generate_bitstream"
puts "Verbose: $verbose"
puts "Timestamp: [clock format [clock seconds] -format "%Y-%m-%d %H:%M:%S"]"
puts ""

# Validate project path
if {$project_path == ""} {
    puts "ERROR: No project path provided"
    puts "Usage: vivado -mode batch -source generate_bitstream.tcl -tclargs <project_path> [output_dir] [jobs] [synthesis] [implementation] [bitstream] [verbose]"
    exit 1
}

# Check if project file exists
if {![file exists $project_path]} {
    puts "ERROR: Project file not found: $project_path"
    exit 1
}

puts "Project file found: $project_path"

# Create output directory if it doesn't exist
if {![file exists $output_dir]} {
    puts "Creating output directory: $output_dir"
    file mkdir $output_dir
}

# Open project
puts ""
puts "Opening project..."
open_project $project_path

# Get project information
set project_name [get_property NAME [current_project]]
set project_dir [get_property DIRECTORY [current_project]]
set project_part [get_property PART [current_project]]

puts "Project Information:"
puts "  Name: $project_name"
puts "  Directory: $project_dir"
puts "  Part: $project_part"

# Get current runs
set synth_runs [get_runs synth_*]
set impl_runs [get_runs impl_*]

puts ""
puts "Available Runs:"
puts "  Synthesis Runs: [llength $synth_runs]"
foreach run $synth_runs {
    puts "    - $run"
}
puts "  Implementation Runs: [llength $impl_runs]"
foreach run $impl_runs {
    puts "    - $run"
}

# Select runs to use
set synth_run "synth_1"
set impl_run "impl_1"

if {[llength $synth_runs] > 0} {
    set synth_run [lindex $synth_runs 0]
}

if {[llength $impl_runs] > 0} {
    set impl_run [lindex $impl_runs 0]
}

puts ""
puts "Selected Runs:"
puts "  Synthesis: $synth_run"
puts "  Implementation: $impl_run"

# Update compile order
puts ""
puts "Updating compile order..."
update_compile_order -fileset sources_1

# Run synthesis
if {$run_synthesis} {
    puts ""
    puts "=== Running Synthesis ==="
    puts "Starting synthesis run: $synth_run"
    
    set start_time [clock seconds]
    
    # Launch synthesis
    launch_runs $synth_run -jobs $jobs
    
    # Wait for synthesis to complete
    puts "Waiting for synthesis to complete..."
    wait_on_run $synth_run
    
    set end_time [clock seconds]
    set synth_duration [expr $end_time - $start_time]
    
    # Check synthesis result
    set synth_status [get_property STATUS $synth_run]
    puts "Synthesis completed in ${synth_duration} seconds"
    puts "Synthesis Status: $synth_status"
    
    if {$synth_status == "synth_design Complete"} {
        puts "✅ Synthesis completed successfully!"
    } else {
        puts "❌ Synthesis failed!"
        puts "Status: $synth_status"
        
        # Get synthesis log
        set synth_log [get_property LOG_DIRECTORY $synth_run]
        puts "Synthesis log directory: $synth_log"
        
        # Close project and exit with error
        close_project
        exit 1
    }
} else {
    puts "Skipping synthesis (disabled)"
}

# Run implementation
if {$run_implementation} {
    puts ""
    puts "=== Running Implementation ==="
    puts "Starting implementation run: $impl_run"
    
    set start_time [clock seconds]
    
    # Launch implementation
    launch_runs $impl_run -jobs $jobs
    
    # Wait for implementation to complete
    puts "Waiting for implementation to complete..."
    wait_on_run $impl_run
    
    set end_time [clock seconds]
    set impl_duration [expr $end_time - $start_time]
    
    # Check implementation result
    set impl_status [get_property STATUS $impl_run]
    puts "Implementation completed in ${impl_duration} seconds"
    puts "Implementation Status: $impl_status"
    
    if {$impl_status == "route_design Complete"} {
        puts "✅ Implementation completed successfully!"
    } else {
        puts "❌ Implementation failed!"
        puts "Status: $impl_status"
        
        # Get implementation log
        set impl_log [get_property LOG_DIRECTORY $impl_run]
        puts "Implementation log directory: $impl_log"
        
        # Close project and exit with error
        close_project
        exit 1
    }
} else {
    puts "Skipping implementation (disabled)"
}

# Generate bitstream
if {$generate_bitstream} {
    puts ""
    puts "=== Generating Bitstream ==="
    puts "Starting bitstream generation..."
    
    set start_time [clock seconds]
    
    # Launch bitstream generation
    launch_runs $impl_run -to_step write_bitstream -jobs $jobs
    
    # Wait for bitstream generation to complete
    puts "Waiting for bitstream generation to complete..."
    wait_on_run $impl_run
    
    set end_time [clock seconds]
    set bitstream_duration [expr $end_time - $start_time]
    
    # Check bitstream generation result
    set bitstream_status [get_property STATUS $impl_run]
    puts "Bitstream generation completed in ${bitstream_duration} seconds"
    puts "Bitstream Status: $bitstream_status"
    
    if {$bitstream_status == "write_bitstream Complete"} {
        puts "✅ Bitstream generated successfully!"
        
        # Find generated bitstream
        set bitstream_files [glob -nocomplain "$project_dir/$impl_run/*.bit"]
        if {[llength $bitstream_files] > 0} {
            set bitstream_file [lindex $bitstream_files 0]
            set bitstream_name [file tail $bitstream_file]
            
            puts "Generated bitstream: $bitstream_file"
            
            # Copy bitstream to output directory
            set output_bitstream "$output_dir/$bitstream_name"
            file copy -force $bitstream_file $output_bitstream
            puts "Bitstream copied to: $output_bitstream"
            
            # Get bitstream information
            set bitstream_size [file size $output_bitstream]
            puts "Bitstream size: [expr $bitstream_size / 1024] KB"
            
        } else {
            puts "WARNING: Could not find generated bitstream file"
        }
        
    } else {
        puts "❌ Bitstream generation failed!"
        puts "Status: $bitstream_status"
        
        # Close project and exit with error
        close_project
        exit 1
    }
} else {
    puts "Skipping bitstream generation (disabled)"
}

# Generate timing report
puts ""
puts "=== Generating Timing Report ==="
set timing_report "$output_dir/timing_report_[clock format [clock seconds] -format "%Y%m%d_%H%M%S"].txt"

set timing_fp [open $timing_report w]
puts $timing_fp "Timing Report for $project_name"
puts $timing_fp "Generated: [clock format [clock seconds] -format "%Y-%m-%d %H:%M:%S"]"
puts $timing_fp ""

# Get timing information
set timing_paths [get_timing_paths]
puts $timing_fp "Total Timing Paths: [llength $timing_paths]"

# Get worst negative slack
set wns [get_property WNS [get_runs $impl_run]]
puts $timing_fp "Worst Negative Slack: $wns ns"

# Get total negative slack
set tns [get_property TNS [get_runs $impl_run]]
puts $timing_fp "Total Negative Slack: $tns ns"

# Get hold violations
set hold_violations [get_property HOLD_VIOLATIONS [get_runs $impl_run]]
puts $timing_fp "Hold Violations: $hold_violations"

close $timing_fp
puts "Timing report saved to: $timing_report"

# Generate utilization report
puts ""
puts "=== Generating Utilization Report ==="
set util_report "$output_dir/utilization_report_[clock format [clock seconds] -format "%Y%m%d_%H%M%S"].txt"

set util_fp [open $util_report w]
puts $util_fp "Utilization Report for $project_name"
puts $util_fp "Generated: [clock format [clock seconds] -format "%Y-%m-%d %H:%M:%S"]"
puts $util_fp ""

# Get utilization information
set util_report_data [report_utilization -return_string]
puts $util_fp $util_report_data

close $util_fp
puts "Utilization report saved to: $util_report"

# Generate summary report
puts ""
puts "=== Generating Summary Report ==="
set summary_report "$output_dir/build_summary_[clock format [clock seconds] -format "%Y%m%d_%H%M%S"].txt"

set summary_fp [open $summary_report w]
puts $summary_fp "Build Summary for $project_name"
puts $summary_fp "Generated: [clock format [clock seconds] -format "%Y-%m-%d %H:%M:%S"]"
puts $summary_fp ""
puts $summary_fp "Project Information:"
puts $summary_fp "  Name: $project_name"
puts $summary_fp "  Part: $project_part"
puts $summary_fp "  Output Directory: $output_dir"
puts $summary_fp ""
puts $summary_fp "Build Configuration:"
puts $summary_fp "  Jobs: $jobs"
puts $summary_fp "  Synthesis: $run_synthesis"
puts $summary_fp "  Implementation: $run_implementation"
puts $summary_fp "  Bitstream: $generate_bitstream"
puts $summary_fp ""
puts $summary_fp "Results:"
puts $summary_fp "  Synthesis Status: $synth_status"
puts $summary_fp "  Implementation Status: $impl_status"
puts $summary_fp "  Bitstream Status: $bitstream_status"
puts $summary_fp "  Worst Negative Slack: $wns ns"
puts $summary_fp "  Total Negative Slack: $tns ns"
puts $summary_fp "  Hold Violations: $hold_violations"
puts $summary_fp ""
puts $summary_fp "Generated Files:"
puts $summary_fp "  Timing Report: $timing_report"
puts $summary_fp "  Utilization Report: $util_report"
puts $summary_fp "  Summary Report: $summary_report"

if {[info exists output_bitstream]} {
    puts $summary_fp "  Bitstream: $output_bitstream"
}

puts $summary_fp ""
puts $summary_fp "Build Status: SUCCESS"
close $summary_fp

puts "Summary report saved to: $summary_report"

# Close project
puts ""
puts "Closing project..."
close_project

puts ""
puts "=== Build Complete ==="
puts "Project: $project_name"
puts "Part: $project_part"
puts "Status: SUCCESS"
puts "Reports: $output_dir"

puts "Script completed successfully"
exit 0
