"""
    peptideMaker generates mutations for a given PDB file using FoldX
    GitHub repository: https://github.com/pepamengual/peptideMaker
    Author: Pep Amengual-Rigo
    Author contact: pepamengualrigo@gmail.com
    Author GitHub: https://github.com/pepamengual/
"""

import subprocess
import os
from multiprocessing import Pool
import shutil

def read_peptides_to_model(peptides_to_model_file):
    """ Returns a list of peptides to model
        Reads a file that contains a single column, being the peptide sequence to model
    """
    peptides_to_model_list = set()
    with open(peptides_to_model_file, "r") as f:
        for line in f:
            line = line.rstrip().split()
            peptide = line[0]
            peptides_to_model_list.add(peptide)
    peptides_to_model_list = list(peptides_to_model_list)
    return peptides_to_model_list

def build_mutation_files(peptide_models_folder, peptides_to_model_list, rotabase_path, foldx_name_file, pdb, peptide_sequence_from_pdb_foldx):
    """
        Goes to working directory
        Creates a copy of the template PDB file, and the rotabase file (needed by foldx in this folder)
        Creates the individual_list.txt file (variable foldx_name_file) containing the mutations ordered by the peptide list
    """
    os.chdir(peptide_models_folder) # A new folder is created by each peptide to be modelled
    for peptide in peptides_to_model_list:
        if not os.path.exists(peptide):
            os.makedirs(peptide)
        shutil.copy("../{}".format(pdb), peptide) # The PDB file to work with is copied into the peptide folder created above
        shutil.copy(rotabase_path, peptide) # The rotabase file of FoldX is also copied into the peptide folder created above
        os.chdir(peptide)
        sequence_to_mutate = peptide_sequence_from_pdb_foldx.format(*tuple(peptide)) # Foldx needs this, will be saved in a file
        with open(foldx_name_file, "w") as f: # Saving the foldx file, individual_list.txt with sequence_to_mutate
            f.write(sequence_to_mutate + '\n')
        os.chdir("..")
    os.chdir("..")

def generate_structural_models(pdb, peptide_models_folder, peptide):
    """
        Ran by multiprocessing_run_of_models
        Goes to work directory, then to peptide directory
        Calls a subprocess of the foldx run
    """
    os.chdir(peptide_models_folder)
    os.chdir(peptide)
    subp = subprocess.Popen(['/home/pepamengual/foldx/foldx2/foldx', '--command=BuildModel', '--pdb='+ pdb +'', '--clean-mode=2', '--mutant-file=individual_list.txt'])
    subp.communicate()
    os.chdir("..")
    os.chdir("..")

def multiprocessing_run_of_models(peptides_to_model_list, processors, peptide_models_folder, pdb):
    """
        Generates multiprocessing pool to create different models at the same time
        Runs the function generate_structural_models()
    """
    pool = Pool(processes=processors)
    multiple_results = []
    for peptide in peptides_to_model_list:
        multiple_results.append(pool.apply_async(generate_structural_models, (pdb, peptide_models_folder, peptide)))
    for result in multiple_results:
        get_result = result.get()

def change_names(peptide_models_folder, peptides_to_model_list, pdb):
    """
        Copies the file generated by foldx into a pdb file named by the peptide sequence
    """
    pdb = pdb.split(".pdb")[0]
    os.chdir(peptide_models_folder)
    for peptide in peptides_to_model_list:
        os.chdir(peptide)
        shutil.copy("{}_1.pdb".format(pdb), "{}.pdb".format(peptide))
        os.chdir("..")

def main():
    ### GLOBAL VARIABLES ###
    peptides_to_model_file = "input_file.txt" # File contianing the peptide column to model
    foldx_name_file = "individual_list.txt" # This file must be named like this to be read by FoldX
    pdb = "3PWN_Repair.pdb" # PDB name to work with
    rotabase_path = "/home/pepamengual/def_neoantigens/new/models/rotabase.txt" # Path to the rotabase file
    processors = 3 # How many processors you want to use
    peptide_models_folder = "foldx_models" # Name of the folder to save the files
    
    ### PEPTIDE SEQUENCE FOLDX FORMAT ###
    # IMPORTANT: peptide_sequenve_from_pdb_foldx must be changed accorting to the peptide sequence in the PDB file
    # IMPORTANT: first letter means residue in one single letter code
    # IMPORTANT: second letter means chain
    # IMPORTANT: third letter means amino acid position
    
    peptide_sequence_from_pdb_foldx = "LL1{},LL2{},YL3{},GL4{},FL5{},VL6{},NL7{},YL8{},IL9{};" #Modify it according the instructions above

    ### CREATE SIMULATION FOLDER ###
    if not os.path.exists(peptide_models_folder): # Create the simulation folder if not available
        os.makedirs(peptide_models_folder)

    ### RUNNING ###
    peptides_to_model_list = read_peptides_to_model(peptides_to_model_file)
    build_mutation_files(peptide_models_folder, peptides_to_model_list, rotabase_path, foldx_name_file, pdb, peptide_sequence_from_pdb_foldx)
    multiprocessing_run_of_models(peptides_to_model_list, processors, peptide_models_folder, pdb)
    change_names(peptide_models_folder, peptides_to_model_list, pdb)

if __name__ == "__main__":
    main()
