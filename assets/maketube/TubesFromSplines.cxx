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

    // **直線のパラメータ**
    int numPoints = 100;  // 中心線の点の数
    double length = 100.0; // 直線の長さ
    double radius = 5.0;   // デフォルトの半径
    double zStep = length / (numPoints - 1); // z方向のステップサイズ

    // **直線の中心線を作成**
    for (int i = 0; i < numPoints; ++i)
    {
        double x = 0.0;
        double y = 0.0;
        double z = i * zStep;
        points->InsertPoint(i, x, y, z);
    }

    // **スプライン補間**
    vtkNew<vtkParametricSpline> spline;
    spline->SetPoints(points);
    vtkNew<vtkParametricFunctionSource> functionSource;
    functionSource->SetParametricFunction(spline);
    functionSource->SetUResolution(10 * points->GetNumberOfPoints());
    functionSource->Update();

    // === CSV 出力 ===
    std::ofstream csvFile("helix_centerline.csv");
    if (!csvFile) {
        std::cerr << "Error: Cannot open file for writing CSV." << std::endl;
        return EXIT_FAILURE;
    }

    csvFile << "x,y,z\n";
    auto tubePolyData = functionSource->GetOutput();
    for (unsigned int i = 0; i < tubePolyData->GetNumberOfPoints(); ++i)
    {
        double p[3];
        tubePolyData->GetPoint(i, p);
        csvFile << p[0] << "," << p[1] << "," << p[2] << "\n";
    }
    csvFile.close();
    std::cout << "CSV file saved as 'helix_centerline.csv'" << std::endl;

    // === **Z座標に基づいた半径変化（中央部に狭窄を作る）** ===
    vtkNew<vtkDoubleArray> tubeRadius;
    unsigned int n = functionSource->GetOutput()->GetNumberOfPoints();
    tubeRadius->SetNumberOfTuples(n);
    tubeRadius->SetName("TubeRadius");

    double zMin = 0.0;      // 直線の下端
    double zMax = length;   // 直線の上端
    double narrowCenter = 50.0;  // 狭窄の中心 (Z=50)
    double narrowWidth = 20.0;   // 狭窄の幅（±5）

    for (unsigned int i = 0; i < n; ++i)
    {
        double p[3];
        tubePolyData->GetPoint(i, p);
        double z = p[2];  // Z座標

        double r = 5.0; // デフォルトの半径

        // **中央付近（Z=50±5）のみ半径を5次関数で変化**
        if (z >= (narrowCenter - narrowWidth / 2) && z <= (narrowCenter + narrowWidth / 2))
        {
            double t = (z - (narrowCenter - narrowWidth / 2)) / narrowWidth; // 0.0〜1.0 の範囲
            r = 5.0 - 48 * pow(t, 2) + 96 * pow(t, 3) - 48 * pow(t, 4);
        }

        tubeRadius->SetTuple1(i, r);
    }

    // **スカラー値を適用**
    tubePolyData->GetPointData()->AddArray(tubeRadius);
    tubePolyData->GetPointData()->SetActiveScalars("TubeRadius");

    // **チューブ形状を生成**
    vtkNew<vtkTubeFilter> tuber;
    tuber->SetInputData(tubePolyData);
    tuber->SetNumberOfSides(20);
    tuber->SetVaryRadiusToVaryRadiusByAbsoluteScalar();

    // **STLファイルに書き出し**
    vtkNew<vtkSTLWriter> writer;
    writer->SetFileName("helix_output_variable_radius.stl");
    writer->SetInputConnection(tuber->GetOutputPort());
    writer->Write();

    std::cout << "STL file saved as 'helix_output_variable_radius.stl'" << std::endl;

    //-------------- 可視化の設定 --------------
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
    renderWindow->SetWindowName("Straight Tube with Variable Radius");

    vtkNew<vtkRenderWindowInteractor> renderWindowInteractor;
    renderWindowInteractor->SetRenderWindow(renderWindow);
    renderer->AddActor(tubeActor);
    renderer->SetBackground(colors->GetColor3d("SlateGray").GetData());

    renderWindow->Render();
    renderWindowInteractor->Start();

    return EXIT_SUCCESS;
}




