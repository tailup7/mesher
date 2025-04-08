#define _USE_MATH_DEFINES
#include <cmath>
#include <iostream>
#include <fstream>
#include <vtkActor.h>
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

    // **パラメータ設定**
    int numStraightPoints = 20;  // 直線部分の点の数
    int numCurvePoints = 100;    // 曲がり管の点の数
    double R = 50.0;             // 曲率半径
    double thetaMax = 90.0;       // 円弧の角度 (90°)
    double thetaStep = thetaMax / (numCurvePoints - 1); // 角度のステップサイズ
    double L = 50.0;             // 直線の長さ

    // **開始直線（円弧の接線方向に沿う）**
    for (int i = 0; i < numStraightPoints; ++i)
    {
        double x = -L + (L / (numStraightPoints - 1)) * i;
        double y = R ;
        double z = 0.0;
        points->InsertPoint(i, x, y, z);
    }

    // **円弧に沿った中心線を作成**
    int startIndex = numStraightPoints;
    for (int i = 0; i < numCurvePoints; ++i)
    {
        double theta = (thetaStep * i) * (M_PI / 180.0); // ラジアン変換
        double x = R * sin(theta);
        double y = R * cos(theta);
        double z = 0.0;
        points->InsertPoint(startIndex + i, x, y, z);
    }

    // **終了直線（円弧の接線方向に沿う）**
    int endIndex = startIndex + numCurvePoints;
    double thetaEnd = thetaMax * (M_PI / 180.0);
    double dx = -sin(thetaEnd); // X成分
    double dy = cos(thetaEnd);  // Y成分

    for (int i = 0; i < numStraightPoints; ++i)
    {
        double x = R ;
        double y = - (L / (numStraightPoints - 1)) * i ;
        double z = 0.0;
        points->InsertPoint(endIndex + i, x, y, z);
    }

    // **スプライン補間**
    vtkNew<vtkParametricSpline> spline;
    spline->SetPoints(points);
    vtkNew<vtkParametricFunctionSource> functionSource;
    functionSource->SetParametricFunction(spline);
    functionSource->SetUResolution(10 * points->GetNumberOfPoints());
    functionSource->Update();

    // === **CSV 出力（中心線）** ===
    std::ofstream csvFile("bend_extended_centerline.csv");
    if (!csvFile)
    {
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
    std::cout << "CSV file saved as 'bend_extended_centerline.csv'" << std::endl;

    // **チューブ形状を生成**
    vtkNew<vtkTubeFilter> tuber;
    tuber->SetInputData(tubePolyData);
    tuber->SetNumberOfSides(20);
    tuber->SetRadius(5.0); // 半径固定
    tuber->SetVaryRadiusToVaryRadiusByAbsoluteScalar();

    // **STLファイルに書き出し**
    vtkNew<vtkSTLWriter> writer;
    writer->SetFileName("bend_extended_output.stl");
    writer->SetInputConnection(tuber->GetOutputPort());
    writer->Write();

    std::cout << "STL file saved as 'bend_extended_output.stl'" << std::endl;

    // **可視化**
    vtkNew<vtkPolyDataMapper> tubeMapper;
    tubeMapper->SetInputConnection(tuber->GetOutputPort());
    vtkNew<vtkActor> tubeActor;
    tubeActor->SetMapper(tubeMapper);
    vtkNew<vtkNamedColors> colors;
    vtkNew<vtkRenderer> renderer;
    renderer->UseHiddenLineRemovalOn();
    vtkNew<vtkRenderWindow> renderWindow;
    renderWindow->AddRenderer(renderer);
    renderWindow->SetSize(640, 480);
    renderWindow->SetWindowName("Bend Tube with Extended Sections");

    vtkNew<vtkRenderWindowInteractor> renderWindowInteractor;
    renderWindowInteractor->SetRenderWindow(renderWindow);
    renderer->AddActor(tubeActor);
    renderer->SetBackground(colors->GetColor3d("SlateGray").GetData());

    renderWindow->Render();
    renderWindowInteractor->Start();

    return EXIT_SUCCESS;
}







