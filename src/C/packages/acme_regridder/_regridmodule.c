#include <Python.h>
#include "numpy/ndarrayobject.h"
#include <stdbool.h>

static PyObject *
  PyACME_apply_weights_masked(PyObject *self,PyObject *args)
{
  PyObject *row_obj,*col_obj,*S_obj,*data_obj;
  PyArrayObject *row=NULL,*col=NULL,*S=NULL,*dest_field=NULL,*data=NULL;
  double *S_vals;
  int *row_vals,*col_vals;
  char type;
  void *data_vals;
  double *out;
  bool *is_missing;
  PyObject *Missing;
  double missingd;
  float missingf;
  int missingi;
  long missingl;
  int n2;

  if (!PyArg_ParseTuple(args,"OOOOiO",&data_obj,&S_obj,&row_obj,&col_obj,&n2,&Missing))
    return NULL;

    S =(PyArrayObject *) PyArray_FromObject(S_obj,NPY_FLOAT64,1,1);
    col =(PyArrayObject *) PyArray_FromObject(col_obj,NPY_INT32,1,1);
    row =(PyArrayObject *) PyArray_FromObject(row_obj,NPY_INT32,1,1);
    data =(PyArrayObject *) PyArray_FromObject(data_obj,NPY_NOTYPE,1,0);

    type = data->descr->type;

    if ((type=='d') || (type=='f')) {
      if (PyFloat_Check(Missing) == 1 ) {
        missingd = PyFloat_AsDouble(Missing);
        missingf = missingd;
      }
      else {
        return NULL;
      }
    }
    else if ((type=='i') || (type=='l') ) {
      if (PyInt_Check(Missing) == 1) {
        missingl = PyInt_AsLong(Missing);
      }
      else if (PyLong_Check(Missing) == 1) {
        missingl = PyLong_AsLong(Missing);
      }
      else {
        return NULL;
      }
      missingi = (int) missingl;
      missingd = (double) missingl;
    }
    else {
      return NULL;
    }


    int nindep=1;
    int i,j;
    for (i=0;i<data->nd-1;i++) {
      nindep*=data->dimensions[i];
    }
    /* Construct dest array */
    int n1 = data->dimensions[data->nd-1];
    npy_intp newdims[2];
    newdims[0]=nindep;
    newdims[1] = n2;
    out=malloc(newdims[0]*newdims[1]*sizeof(double));
    is_missing=malloc(newdims[0]*newdims[1]*sizeof(bool));
    #pragma omp parallel for
    for (j=0;j<newdims[0]*newdims[1];j++) {
      out[j]=0;
      is_missing[j] = true;
    }

    dest_field = PyArray_SimpleNew(2,newdims,NPY_FLOAT64);

    S_vals = (double *)S->data;
    row_vals = (int *) row->data;
    col_vals = (int *) col->data;
    data_vals = (void *) data->data;
    #pragma omp parallel for private(j) schedule(guided) if (nindep > 5)
    for (i=0;i<nindep;i++) {
        for (j=0;j<S->dimensions[0];j++) {
          if (((float *)data_vals)[i*n1+col_vals[j]] != missingf)  {
            out[i*n2+row_vals[j]] = out[i*n2+row_vals[j]] + (double)S_vals[j]*((float *)data_vals)[i*n1+col_vals[j]];
            is_missing[i*n2+row_vals[j]] = false;
          }
        }
      /*
      for (j=0;j<n2;j++) {
        if (fracb_vals[j]>0.) out[i*n2+j]=out[i*n2+j]/(float)fracb_vals[j];
      }
      */
    }
    #pragma omp parallel for
    for (j=0;j<newdims[0]*newdims[1];j++) {
      if (is_missing[j]) out[j] = missingf;
    }
    dest_field->data=out;
    Py_DECREF(S);
    Py_DECREF(col);
    Py_DECREF(row);
    Py_DECREF(data);
    free(is_missing);
  return Py_BuildValue("N",dest_field);
}
static PyObject *
  PyACME_apply_weights(PyObject *self,PyObject *args)
{
  PyObject *row_obj,*col_obj,*S_obj,*data_obj;
  PyArrayObject *row=NULL,*col=NULL,*S=NULL,*dest_field=NULL,*data=NULL;
  double *S_vals;
  int *row_vals,*col_vals;
  char type;
  void *data_vals;
  double *out;
  int n2;

  if (!PyArg_ParseTuple(args,"OOOOi",&data_obj,&S_obj,&row_obj,&col_obj,&n2))
    return NULL;

    S =(PyArrayObject *) PyArray_FromObject(S_obj,NPY_FLOAT64,1,1);
    col =(PyArrayObject *) PyArray_FromObject(col_obj,NPY_INT32,1,1);
    row =(PyArrayObject *) PyArray_FromObject(row_obj,NPY_INT32,1,1);
    data =(PyArrayObject *) PyArray_FromObject(data_obj,NPY_NOTYPE,1,0);

    type = data->descr->type;

    int nindep=1;
    int i,j;
    for (i=0;i<data->nd-1;i++) {
      nindep*=data->dimensions[i];
    }
    /* Construct dest array */
    int n1 = data->dimensions[data->nd-1];
    npy_intp newdims[2];
    newdims[0]=nindep;
    newdims[1] = n2;
    out=malloc(newdims[0]*newdims[1]*sizeof(double));
    #pragma omp parallel for
    for (j=0;j<newdims[0]*newdims[1];j++) {
      out[j]=0;
    }

    dest_field = PyArray_SimpleNew(2,newdims,NPY_FLOAT64);

    S_vals = (double *)S->data;
    row_vals = (int *) row->data;
    col_vals = (int *) col->data;
    data_vals = (void *) data->data;
    #pragma omp parallel for private(j) schedule(guided) if (nindep > 5)
    for (i=0;i<nindep;i++) {
        for (j=0;j<S->dimensions[0];j++) {
            out[i*n2+row_vals[j]] = out[i*n2+row_vals[j]] + (double)S_vals[j]*((float *)data_vals)[i*n1+col_vals[j]];
        }
      /*
      for (j=0;j<n2;j++) {
        if (fracb_vals[j]>0.) out[i*n2+j]=out[i*n2+j]/(float)fracb_vals[j];
      }
      */
    }
    dest_field->data=out;
    Py_DECREF(S);
    Py_DECREF(col);
    Py_DECREF(row);
    Py_DECREF(data);
  return Py_BuildValue("N",dest_field);
}

static PyMethodDef MyExtractMethods[]= {
  {"apply_weights",PyACME_apply_weights, METH_VARARGS},
  {"apply_weights_masked",PyACME_apply_weights_masked, METH_VARARGS},
  {NULL, NULL} /*sentinel */
};

PyMODINIT_FUNC init_regrid(void)
{
  (void) Py_InitModule("_regrid", MyExtractMethods);
  import_array();
  
}

/* int main(int argc,char **argv) */
/* { */
/*   Py_SetProgramName(argv[0]); */
/*   Py_Initialize(); */
/*   init_cmor(); */
/*   return 0; */
/* } */

