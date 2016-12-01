#!/usr/bin/env python
import sys
import os
import argparse
import avutils.file_processing as fp
import avutils.util as util

def filter_entries(options):
   
    ids_to_include_dict = {} 
    ids_to_exclude_dict = {}
    inclusion_active = False
    exclusion_active = False
    if (len(options.files_with_lines_to_include) > 0):
        inclusion_active = True
        read_ids_into_dict(options.files_with_lines_to_include, ids_to_include_dict, options.files_with_lines_to_include_cols, options.title_present_filter_files)
    if (len(options.files_with_liens_to_exclude) > 0):
        exclusion_active = True
        read_ids_into_dict(options.files_with_liens_to_exclude, ids_to_exclude_dict, options.files_with_liens_to_exclude_cols, options.title_present_filter_files)
    assert (inclusion_active or exclusion_active)    

    for file_with_lines_to_filter in options.files_with_lines_to_filter:
        file_name_parts = util.get_file_name_parts(file_with_lines_to_filter) 
        output_dir = options.output_dir
        if output_dir is None:
           output_dir = file_name_parts.directory  
        output_file_name = output_dir+"/"+file_name_parts.get_transformed_file_path(lambda x: options.output_prefix+x)
        output_file_handle = fp.get_file_handle(output_file_name, 'w')
        
        print "Filtering",file_with_lines_to_filter
        def action(inp_arr,line_number):
            the_id = extract_id(inp_arr, options.files_with_lines_to_filter_cols)
            passes = False
            include = the_id in ids_to_include_dict
            exclude = the_id in ids_to_exclude_dict
            if (exclusion_active==False):
                assert inclusion_active == True
                passes = include
            elif (inclusion_active==False):
                assert exclusion_active == True
                passes = (exclude == False)
            else:
                assert inclusion_active and exclusion_active
                if (exclude_has_precedence):
                    passes = False if exclude else include #include if on the inclusion list UNLESS appears on the exclusion list.
                else:
                    passes = True if include else (exclude==False) #exclude if on the exclusion list UNLESS appears on the inclusion list.
            if passes:
                output_file_handle.write("\t".join(inp_arr)+"\n")
        
        file_handle = fp.get_file_handle(file_with_lines_to_filter)
        if (options.title_present_orig):
            output_file_handle.write(file_handle.readline())
        fp.perform_action_on_each_line_of_file(
            file_handle
            , transformation=fp.default_tab_seppd
            , action=action
            , progress_update=options.progress_update
        )


def read_ids_into_dict(files, the_dict, id_cols, title_present):
    for aFile in files:
        file_handle = fp.get_file_handle(aFile)
        def action(inp_arr, line_number):
            the_id = extract_id(inp_arr,id_cols)
            the_dict[the_id] = 1
        fp.perform_action_on_each_line_of_file(
            file_handle
            , transformation = fp.default_tab_seppd
            , action = action
            , ignore_input_title = title_present
        )


def extract_id(inp_arr, id_cols):
    return "_".join([inp_arr[x] for x in id_cols])


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Filters some files according to other files, given that each file has a unique set of 'index' columns. Remember to set a flag if the title is present. By default, assumes column to filter accoridng to is the first one. Also assumes TSVs (tab separated files)")
    parser.add_argument('--title_present_orig', help="title is present on original file", action="store_true")
    parser.add_argument('--title_present_filter_files', help="title is present on files that contain lines to include/exclude", action="store_true")
    parser.add_argument('--files_with_lines_to_filter', nargs='+', required=True)
    parser.add_argument('--files_with_lines_to_include', nargs='+', default=[])
    parser.add_argument('--files_with_liens_to_exclude', nargs='+', default=[])
    parser.add_argument('--files_with_lines_to_filter_cols', nargs='+', help="Column indexes forming unique identifier in the files to filter", type=int, default=[0])
    parser.add_argument('--files_with_lines_to_include_cols', nargs='+', type=int, default=[0])
    parser.add_argument('--files_with_liens_to_exclude_cols', nargs='+', type=int, default=[0])
    parser.add_argument('--exclude_has_precedence', help="Include this flag to make exclusion take precedence over inclusion, for when a line appears in both", action="store_true")
    parser.add_argument('--output_prefix', default='filtered_')
    parser.add_argument('--output_dir',help="Will default to the same directory that the input file to be filtered lives in")
    parser.add_argument('--progress_update', type=int, default=10000)
    args = parser.parse_args()
    
    if (len(args.files_with_lines_to_include) and len(args.files_with_liens_to_exclude)):
        print "At least one of files_with_lines_to_include or files_with_liens_to_exclude should be provided"
        sys.exit(1)
    
    filter_entries(parser.parse_args())
