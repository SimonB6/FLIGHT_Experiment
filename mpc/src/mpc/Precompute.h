#pragma once

#include "../globals.h"

#include "../mpc/AESObject.h"

#include "../gpu/DeviceData.h"
#include "../gpu/gemm.cuh"
#include "../gpu/conv.cuh"

extern std::vector<AESObject*> aes_objects;

extern Profiler comm_profiler;
extern Profiler func_profiler;
extern Profiler test_profiler;

class Precompute
{
    private:
	    void initialize();

    public:
        Precompute();
        ~Precompute();

        template<typename T, typename Share>
        void getRandomNumber(Share &r);

        template<typename T>
        void getRandomNumber(DeviceData<T> &r);

        template<typename T, typename Share>
        void getCoin(Share &r);

        template<typename T>
        void getCoin(DeviceData<T> &r);

        template<typename T, typename Share>
        void getConvBeaverTriple_fprop(Share &x, Share &y, Share &z,
            int batchSize, int imageHeight, int imageWidth, int Din,
            int Dout, int filterHeight, int filterWidth,
            int paddingHeight, int paddingWidth,
            int stride, int dilation);

        template<typename T, typename Share>
        void getConvBeaverTriple_dgrad(Share &x, Share &y, Share &z,
            int batchSize, int outputHeight, int outputWidth, int Dout,
            int filterHeight, int filterWidth, int Din,
            int paddingHeight, int paddingWidth, int stride, int dilation,
            int imageHeight, int imageWidth);

        template<typename T, typename Share>
        void getConvBeaverTriple_wgrad(Share &x, Share &y, Share &z,
            int batchSize, int outputHeight, int outputWidth, int Dout,
            int imageHeight, int imageWidth, int Din,
            int filterHeight, int filterWidth,
            int paddingHeight, int paddingWidth, int stride, int dilation);

        template<typename T, typename Share>
        void getMatrixBeaverTriple(Share &x, Share &y, Share &z,
            int a_rows, int a_cols, int b_rows, int b_cols,
            bool transpose_a, bool transpose_b, bool transpose_c);

        template<typename T, typename Share>
        void getBooleanBeaverTriples(Share &x, Share &y, Share &z);

        template<typename T, typename Share>
        void getBeaverTriples(Share &x, Share &y, Share &z);

        // Currently, r = 3 and rPrime = 3 * 2^d
        template<typename T, typename Share>
        void getDividedShares(Share &r, Share &rPrime,
                uint64_t d, size_t size) {

            assert(r.size() == size && "r.size is incorrect");
            assert(rPrime.size() == size && "rPrime.size is incorrect");

            // TODO use random numbers

            rPrime.fill(d);
            r.fill(1);
        }
        
        // Currently, r = 3 and rPrime = 3 * 2^d
        template<typename T, typename I, typename Share>
        void getDividedShares(Share &r, Share &rPrime,
                DeviceData<T, I> &d, size_t size) {

            assert(r.size() == size && "r.size is incorrect");
            assert(rPrime.size() == size && "rPrime.size is incorrect");

            // TODO use random numbers

            rPrime.zero();
            rPrime += d;
            r.fill(1);
        }

        template<typename T, typename ShareBase, typename Share>
        void getCorrelatedRandomness(
            const ShareBase& w, Share& out1, Share& out2
        );

        template<typename T, typename Share>
        void getCorrelatedRandomness_matmul(
            const Share& w, Share& out1, Share& out2,
            int a_rows, int a_cols, int b_rows, int b_cols,
            bool transpose_a, bool transpose_b, bool transpose_c
        );

        template<typename T, typename Share>
        void getCorrelatedRandomness_fprop(
            const Share& w, Share& out1, Share& out2,
            int batchSize, int imageHeight, int imageWidth, int Din,
            int Dout, int filterHeight, int filterWidth,
            int paddingHeight, int paddingWidth,
            int stride, int dilation
        );

        template<typename T, typename ShareBase1, typename ShareBase2, typename Share>
        void getCorrelatedPairs(
            const ShareBase1& in, ShareBase2& out
        );

        template<typename T, typename Share>
        void getCorrelatedPairs_matmul(
            const Share& in, Share& out,
            int a_rows, int a_cols, int b_rows, int b_cols,
            bool transpose_a, bool transpose_b, bool transpose_c
        );

        template<typename T, typename Share>
        void getCorrelatedPairs_fprop(
            const Share& in, Share& out,
            int batchSize, int imageHeight, int imageWidth, int Din,
            int Dout, int filterHeight, int filterWidth,
            int paddingHeight, int paddingWidth,
            int stride, int dilation
        );

        template<typename T, typename Share, typename Share2>
        void reshareC_off(
            const Share& in, Share2& out
        );

        template<typename T, typename Share, typename Share2, typename Share3, typename Share4>
        void FusionMux_off(
            const Share& x, const Share2& tb,
            Share2& dbdx, Share2& db, Share3& bang, Share4& z
        );
};

#include "Precompute.inl"  