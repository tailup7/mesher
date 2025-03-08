#define _USE_MATH_DEFINES
#include <cmath>
#include <iostream>
#include <fstream>  
#include <vtkActor.h>
#include <vtkDoubleArray.h>
#include <vtkNamedColors.h>
#include <vtkNew.h>
#include <vtkParametricFunctionSource.h>
#include <vtkParametricSpline.h>
#include <vtkPointData.h>
#include <vtkPoints.h>
#include <vtkPolyDataMapper.h>
#include <vtkProperty.h>
#include <vtkRenderWindow.h>
#include <vtkRenderWindowInteractor.h>
#include <vtkRenderer.h>
#include <vtkTubeFilter.h>
#include <vtkSTLWriter.h>

int main(int, char* [])
{
    vtkNew<vtkPoints> points;

    // �点��̃p�����[�^
    int numTurns = 3;     // �点��̊�����
    int numPoints = 100;  // 1�̂点��ɂ�����|�C���g��
    double radius = 10.0;  // ���a
    double height = 100.0; // �点��̍���
    double angleStep = 2 * M_PI / (numPoints / numTurns);  // �p�x�̃X�e�b�v�T�C�Y

    for (int i = 0; i < numPoints; ++i)
    {
        double theta = i * angleStep;  // �p�x (���W�A��)
        double x = radius * cos(theta);
        double y = radius * sin(theta);
        double z = (height / (numTurns * 2 * M_PI)) * theta;  // ���������ɏ㏸
        points->InsertPoint(i, x, y, z);
    }

    // �X�v���C�����
    vtkNew<vtkParametricSpline> spline;
    spline->SetPoints(points);
    vtkNew<vtkParametricFunctionSource> functionSource;
    functionSource->SetParametricFunction(spline);
    functionSource->SetUResolution(10 * points->GetNumberOfPoints());
    functionSource->Update();

    // === CSV �o�͂�ǉ� ===
    std::ofstream csvFile("helix_centerline.csv");
    if (!csvFile) {
        std::cerr << "Error: Cannot open file for writing CSV." << std::endl;
        return EXIT_FAILURE;
    }

    csvFile << "x,y,z\n"; // �w�b�_�[�s��ǉ�
    auto tubePolyData = functionSource->GetOutput();
    for (unsigned int i = 0; i < tubePolyData->GetNumberOfPoints(); ++i)
    {
        double p[3];
        tubePolyData->GetPoint(i, p);  // x, y, z ���擾
        csvFile << p[0] << "," << p[1] << "," << p[2] << "\n"; // CSV �ɏ�������
    }
    csvFile.close();
    std::cout << "CSV file saved as 'helix_centerline.csv'" << std::endl;
    // === �����܂� CSV �o�� ===

    // ���a���̃X�J���[�l�𐶐�
    vtkNew<vtkDoubleArray> tubeRadius;
    unsigned int n = functionSource->GetOutput()->GetNumberOfPoints();
    tubeRadius->SetNumberOfTuples(n);
    tubeRadius->SetName("TubeRadius");
    double r = 2.0;  // ���a������
    for (unsigned int i = 0; i < n; ++i)
    {
        tubeRadius->SetTuple1(i, r);
    }

    // �X�J���[�l��K�p
    tubePolyData->GetPointData()->AddArray(tubeRadius);
    tubePolyData->GetPointData()->SetActiveScalars("TubeRadius");

    // �`���[�u�`��𐶐�
    vtkNew<vtkTubeFilter> tuber;
    tuber->SetInputData(tubePolyData);
    tuber->SetNumberOfSides(20);
    tuber->SetVaryRadiusToVaryRadiusByAbsoluteScalar();

    // STL�t�@�C���ɏ����o��
    vtkNew<vtkSTLWriter> writer;
    writer->SetFileName("helix_output.stl");
    writer->SetInputConnection(tuber->GetOutputPort());
    writer->Write();

    std::cout << "STL file saved as 'helix_output.stl'" << std::endl;

    //-------------- �����̐ݒ� --------------
    vtkNew<vtkPolyDataMapper> tubeMapper;
    tubeMapper->SetInputConnection(tuber->GetOutputPort());
    tubeMapper->SetScalarRange(tubePolyData->GetScalarRange());

    vtkNew<vtkActor> tubeActor;
    tubeActor->SetMapper(tubeMapper);
    tubeActor->GetProperty()->SetOpacity(0.6);

    vtkNew<vtkNamedColors> colors;
    vtkNew<vtkRenderer> renderer;
    renderer->UseHiddenLineRemovalOn();
    vtkNew<vtkRenderWindow> renderWindow;
    renderWindow->AddRenderer(renderer);
    renderWindow->SetSize(640, 480);
    renderWindow->SetWindowName("HelixTube");

    vtkNew<vtkRenderWindowInteractor> renderWindowInteractor;
    renderWindowInteractor->SetRenderWindow(renderWindow);
    renderer->AddActor(tubeActor);
    renderer->SetBackground(colors->GetColor3d("SlateGray").GetData());

    renderWindow->Render();
    renderWindowInteractor->Start();

    return EXIT_SUCCESS;
}


