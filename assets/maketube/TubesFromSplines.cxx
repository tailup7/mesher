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

    // らせんのパラメータ
    int numTurns = 3;     // らせんの巻き数
    int numPoints = 100;  // 中心線点数を決める要因の1つ
    double radius = 10.0;  // 半径
    double height = 100.0; // らせんの高さ
    double angleStep = 2 * M_PI / (numPoints / numTurns);  // 角度のステップサイズ

    for (int i = 0; i < numPoints; ++i)
    {
        double theta = i * angleStep;  // 角度 (ラジアン)
        double x = radius * cos(theta);
        double y = radius * sin(theta);
        double z = (height / (numTurns * 2 * M_PI)) * theta;  // 高さを一定に上昇
        points->InsertPoint(i, x, y, z);
    }

    // スプライン補間
    vtkNew<vtkParametricSpline> spline;
    spline->SetPoints(points);
    vtkNew<vtkParametricFunctionSource> functionSource;
    functionSource->SetParametricFunction(spline);
    functionSource->SetUResolution(10 * points->GetNumberOfPoints()); // 中心線の点の数を増やす
    functionSource->Update();

    // === CSV 出力を追加 ===
    std::ofstream csvFile("helix_centerline.csv");
    if (!csvFile) {
        std::cerr << "Error: Cannot open file for writing CSV." << std::endl;
        return EXIT_FAILURE;
    }

    csvFile << "x,y,z\n"; // ヘッダー行を追加
    auto tubePolyData = functionSource->GetOutput();
    for (unsigned int i = 0; i < tubePolyData->GetNumberOfPoints(); ++i)
    {
        double p[3];
        tubePolyData->GetPoint(i, p);  // x, y, z を取得
        csvFile << p[0] << "," << p[1] << "," << p[2] << "\n"; // CSV に書き込む
    }
    csvFile.close();
    std::cout << "CSV file saved as 'helix_centerline.csv'" << std::endl;

    // === 特定範囲の半径を5次関数で変更 ===
    vtkNew<vtkDoubleArray> tubeRadius;
    unsigned int n = functionSource->GetOutput()->GetNumberOfPoints();
    tubeRadius->SetNumberOfTuples(n);
    tubeRadius->SetName("TubeRadius");

    // 特定範囲を指定
    int startIndex = 500;  // 変化を適用する開始点
    int endIndex = 550;    // 変化を適用する終了点

    for (unsigned int i = 0; i < n; ++i)
    {
        double r = 2.0; // デフォルトの半径

        // 中心線インデックスが 500~550 の範囲の場合のみ 5次関数を適用
        if (i >= startIndex && i <= endIndex)
        {
            double t = static_cast<double>(i - startIndex) / (endIndex - startIndex); // 0.0 〜 1.0 の範囲
            r = 2.0 -24 *  pow(t, 2) + 48 * pow(t,3) - 24 * pow(t, 4) ; // 5次関数の定義
        }

        tubeRadius->SetTuple1(i, r);
    }

    // スカラー値を適用
    tubePolyData->GetPointData()->AddArray(tubeRadius);
    tubePolyData->GetPointData()->SetActiveScalars("TubeRadius");

    // チューブ形状を生成
    vtkNew<vtkTubeFilter> tuber;
    tuber->SetInputData(tubePolyData);
    tuber->SetNumberOfSides(20);
    tuber->SetVaryRadiusToVaryRadiusByAbsoluteScalar();

    // STLファイルに書き出し
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
    renderWindow->SetWindowName("HelixTube with Variable Radius");

    vtkNew<vtkRenderWindowInteractor> renderWindowInteractor;
    renderWindowInteractor->SetRenderWindow(renderWindow);
    renderer->AddActor(tubeActor);
    renderer->SetBackground(colors->GetColor3d("SlateGray").GetData());

    renderWindow->Render();
    renderWindowInteractor->Start();

    return EXIT_SUCCESS;
}



